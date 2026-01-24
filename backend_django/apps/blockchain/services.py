"""
Blockchain services for interacting with smart contracts.

This module provides high-level services for:
- Consortium management (create, add members, vote)
- Model registry operations
- Computation verification

All private keys are fetched from OpenBao/Vault.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from django.conf import settings

from .secrets import (
    BlockchainWallet,
    blockchain_secrets,
    get_consortium_signer_wallet,
    get_deployer_wallet,
    get_rpc_url,
    get_verifier_wallet,
)

logger = logging.getLogger(__name__)

# Contract ABIs path
CONTRACTS_DIR = Path(__file__).parent.parent.parent.parent / "contracts" / "out"


@dataclass
class TransactionResult:
    """Result of a blockchain transaction."""

    success: bool
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    error: Optional[str] = None

    def __bool__(self) -> bool:
        return self.success


class BlockchainService:
    """
    Base service for blockchain interactions.

    Handles Web3 connection, transaction signing, and gas estimation.
    Private keys are fetched from Vault and never stored in memory
    longer than necessary.
    """

    def __init__(self, network: str = "arbitrum_sepolia"):
        self.network = network
        self._web3 = None
        self._chain_id = None

    @property
    def web3(self):
        """Lazy initialization of Web3 connection."""
        if self._web3 is None:
            try:
                from web3 import Web3
                from web3.middleware import ExtraDataToPOAMiddleware

                rpc_url = get_rpc_url(self.network)
                self._web3 = Web3(Web3.HTTPProvider(rpc_url))

                # Add PoA middleware for Arbitrum
                self._web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

                if not self._web3.is_connected():
                    raise ConnectionError(f"Failed to connect to {rpc_url}")

                self._chain_id = self._web3.eth.chain_id
                logger.info(f"Connected to {self.network} (chain_id={self._chain_id})")

            except ImportError:
                raise ImportError("web3 package required. Install with: pip install web3")

        return self._web3

    @property
    def chain_id(self) -> int:
        """Get the chain ID."""
        if self._chain_id is None:
            _ = self.web3  # Initialize connection
        return self._chain_id

    def _load_contract_abi(self, contract_name: str) -> dict:
        """Load contract ABI from compiled artifacts."""
        abi_path = CONTRACTS_DIR / f"{contract_name}.sol" / f"{contract_name}.json"

        if not abi_path.exists():
            # Try v2 path
            abi_path = CONTRACTS_DIR / "v2" / f"{contract_name}.sol" / f"{contract_name}.json"

        if not abi_path.exists():
            raise FileNotFoundError(f"Contract ABI not found: {abi_path}")

        with open(abi_path) as f:
            artifact = json.load(f)
            return artifact.get("abi", artifact)

    def _get_contract(self, address: str, contract_name: str):
        """Get a contract instance."""
        abi = self._load_contract_abi(contract_name)
        return self.web3.eth.contract(
            address=self.web3.to_checksum_address(address),
            abi=abi,
        )

    def _estimate_gas(self, tx: dict) -> int:
        """Estimate gas for a transaction with buffer."""
        estimated = self.web3.eth.estimate_gas(tx)
        # Add 20% buffer
        return int(estimated * 1.2)

    def _build_transaction(
        self,
        wallet: BlockchainWallet,
        to: str,
        data: bytes,
        value: int = 0,
    ) -> dict:
        """Build a transaction dictionary."""
        nonce = self.web3.eth.get_transaction_count(wallet.address)

        tx = {
            "from": wallet.address,
            "to": self.web3.to_checksum_address(to),
            "data": data,
            "value": value,
            "nonce": nonce,
            "chainId": self.chain_id,
        }

        # Estimate gas
        tx["gas"] = self._estimate_gas(tx)

        # Get gas price (EIP-1559 style for Arbitrum)
        latest_block = self.web3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas", self.web3.eth.gas_price)
        max_priority_fee = self.web3.to_wei(0.1, "gwei")

        tx["maxFeePerGas"] = base_fee * 2 + max_priority_fee
        tx["maxPriorityFeePerGas"] = max_priority_fee

        return tx

    def _sign_and_send(self, wallet: BlockchainWallet, tx: dict) -> TransactionResult:
        """Sign and send a transaction."""
        try:
            from eth_account import Account

            # Sign transaction
            if not wallet.private_key.startswith("0x"):
                private_key = f"0x{wallet.private_key}"
            else:
                private_key = wallet.private_key

            signed = Account.sign_transaction(tx, private_key)

            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)

            logger.info(f"Transaction sent: {tx_hash.hex()}")

            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt["status"] == 1:
                return TransactionResult(
                    success=True,
                    tx_hash=tx_hash.hex(),
                    block_number=receipt["blockNumber"],
                    gas_used=receipt["gasUsed"],
                )
            else:
                return TransactionResult(
                    success=False,
                    tx_hash=tx_hash.hex(),
                    error="Transaction reverted",
                )

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return TransactionResult(success=False, error=str(e))

    def get_balance(self, address: str) -> int:
        """Get ETH balance in wei."""
        return self.web3.eth.get_balance(self.web3.to_checksum_address(address))

    def get_balance_eth(self, address: str) -> float:
        """Get ETH balance in ETH."""
        return self.web3.from_wei(self.get_balance(address), "ether")


class ConsortiumService(BlockchainService):
    """
    Service for ConsortiumGovernanceV2 contract interactions.

    All operations use the consortium-signer wallet from Vault.
    """

    CONTRACT_NAME = "ConsortiumGovernanceV2"

    def __init__(self, contract_address: str, network: str = "arbitrum_sepolia"):
        super().__init__(network)
        self.contract_address = contract_address
        self._contract = None

    @property
    def contract(self):
        """Get the contract instance."""
        if self._contract is None:
            self._contract = self._get_contract(self.contract_address, self.CONTRACT_NAME)
        return self._contract

    def create_consortium(
        self,
        name: str,
        min_voting_quorum: int,
        voting_duration: int,
        model_config_hash: bytes,
        wallet: Optional[BlockchainWallet] = None,
    ) -> TransactionResult:
        """
        Create a new consortium.

        Args:
            name: Consortium name
            min_voting_quorum: Minimum voting quorum (1-100)
            voting_duration: Voting duration in seconds
            model_config_hash: Hash of model configuration
            wallet: Optional wallet override

        Returns:
            TransactionResult with consortium ID in logs
        """
        wallet = wallet or get_consortium_signer_wallet()
        if not wallet:
            return TransactionResult(success=False, error="No wallet configured")

        data = self.contract.encodeABI(
            fn_name="createConsortium",
            args=[name, min_voting_quorum, voting_duration, model_config_hash],
        )

        tx = self._build_transaction(wallet, self.contract_address, data.encode() if isinstance(data, str) else data)
        return self._sign_and_send(wallet, tx)

    def add_member(
        self,
        consortium_id: bytes,
        new_member: str,
        wallet: Optional[BlockchainWallet] = None,
    ) -> TransactionResult:
        """Add a member to a consortium."""
        wallet = wallet or get_consortium_signer_wallet()
        if not wallet:
            return TransactionResult(success=False, error="No wallet configured")

        data = self.contract.encodeABI(
            fn_name="addMember",
            args=[consortium_id, self.web3.to_checksum_address(new_member)],
        )

        tx = self._build_transaction(wallet, self.contract_address, data.encode() if isinstance(data, str) else data)
        return self._sign_and_send(wallet, tx)

    def record_contribution(
        self,
        consortium_id: bytes,
        record_count: int,
        feature_count: int,
        data_hash: bytes,
        checksum_hash: bytes,
        wallet: Optional[BlockchainWallet] = None,
    ) -> TransactionResult:
        """Record a data contribution."""
        wallet = wallet or get_consortium_signer_wallet()
        if not wallet:
            return TransactionResult(success=False, error="No wallet configured")

        data = self.contract.encodeABI(
            fn_name="recordContribution",
            args=[consortium_id, record_count, feature_count, data_hash, checksum_hash],
        )

        tx = self._build_transaction(wallet, self.contract_address, data.encode() if isinstance(data, str) else data)
        return self._sign_and_send(wallet, tx)

    def get_consortium(self, consortium_id: bytes) -> dict:
        """Get consortium details."""
        result = self.contract.functions.getConsortium(consortium_id).call()
        return {
            "name": result[0],
            "owner": result[1],
            "status": result[2],
            "member_count": result[3],
            "total_contributions": result[4],
            "min_voting_quorum": result[5],
            "voting_duration": result[6],
        }

    def get_member(self, consortium_id: bytes, address: str) -> dict:
        """Get member details."""
        result = self.contract.functions.getMember(
            consortium_id, self.web3.to_checksum_address(address)
        ).call()
        return {
            "status": result[0],
            "joined_at": result[1],
            "contribution_count": result[2],
            "contribution_weight": result[3],
            "last_contribution_at": result[4],
        }


class ModelRegistryService(BlockchainService):
    """
    Service for ModelRegistryV2 contract interactions.
    """

    CONTRACT_NAME = "ModelRegistryV2"

    def __init__(self, contract_address: str, network: str = "arbitrum_sepolia"):
        super().__init__(network)
        self.contract_address = contract_address
        self._contract = None

    @property
    def contract(self):
        """Get the contract instance."""
        if self._contract is None:
            self._contract = self._get_contract(self.contract_address, self.CONTRACT_NAME)
        return self._contract

    def register_model(
        self,
        model_type: str,
        version: str,
        wallet: Optional[BlockchainWallet] = None,
    ) -> TransactionResult:
        """Register a new ML model."""
        wallet = wallet or get_consortium_signer_wallet()
        if not wallet:
            return TransactionResult(success=False, error="No wallet configured")

        data = self.contract.encodeABI(
            fn_name="registerModel",
            args=[model_type, version],
        )

        tx = self._build_transaction(wallet, self.contract_address, data.encode() if isinstance(data, str) else data)
        return self._sign_and_send(wallet, tx)

    def save_checkpoint(
        self,
        model_id: bytes,
        epoch: int,
        weights_hash: bytes,
        metrics_hash: bytes,
        wallet: Optional[BlockchainWallet] = None,
    ) -> TransactionResult:
        """Save a training checkpoint."""
        wallet = wallet or get_consortium_signer_wallet()
        if not wallet:
            return TransactionResult(success=False, error="No wallet configured")

        data = self.contract.encodeABI(
            fn_name="saveCheckpoint",
            args=[model_id, epoch, weights_hash, metrics_hash],
        )

        tx = self._build_transaction(wallet, self.contract_address, data.encode() if isinstance(data, str) else data)
        return self._sign_and_send(wallet, tx)

    def get_model(self, model_id: bytes) -> dict:
        """Get model details."""
        result = self.contract.functions.getModel(model_id).call()
        return {
            "owner": result[0],
            "model_type": result[1],
            "version": result[2],
            "weights_hash": result[3].hex(),
            "created_at": result[4],
            "updated_at": result[5],
            "verified": result[6],
            "active": result[7],
        }

    def verify_checkpoint(self, model_id: bytes, epoch: int, weights_hash: bytes) -> bool:
        """Verify a checkpoint (O(1) operation)."""
        return self.contract.functions.verifyCheckpoint(model_id, epoch, weights_hash).call()


class ComputationVerifierService(BlockchainService):
    """
    Service for ComputationVerifierV2 contract interactions.
    """

    CONTRACT_NAME = "ComputationVerifierV2"

    def __init__(self, contract_address: str, network: str = "arbitrum_sepolia"):
        super().__init__(network)
        self.contract_address = contract_address
        self._contract = None

    @property
    def contract(self):
        """Get the contract instance."""
        if self._contract is None:
            self._contract = self._get_contract(self.contract_address, self.CONTRACT_NAME)
        return self._contract

    def register_computation(
        self,
        model_id: bytes,
        input_hash: bytes,
        output_hash: bytes,
        proof_hash: bytes = b"\x00" * 32,
        wallet: Optional[BlockchainWallet] = None,
    ) -> TransactionResult:
        """Register a computation result."""
        wallet = wallet or get_consortium_signer_wallet()
        if not wallet:
            return TransactionResult(success=False, error="No wallet configured")

        data = self.contract.encodeABI(
            fn_name="registerComputation",
            args=[model_id, input_hash, output_hash, proof_hash],
        )

        tx = self._build_transaction(wallet, self.contract_address, data.encode() if isinstance(data, str) else data)
        return self._sign_and_send(wallet, tx)

    def register_batch(
        self,
        model_id: bytes,
        input_hashes: list[bytes],
        output_hashes: list[bytes],
        wallet: Optional[BlockchainWallet] = None,
    ) -> TransactionResult:
        """Register a batch of computations."""
        wallet = wallet or get_consortium_signer_wallet()
        if not wallet:
            return TransactionResult(success=False, error="No wallet configured")

        data = self.contract.encodeABI(
            fn_name="registerBatch",
            args=[model_id, input_hashes, output_hashes],
        )

        tx = self._build_transaction(wallet, self.contract_address, data.encode() if isinstance(data, str) else data)
        return self._sign_and_send(wallet, tx)

    def verify_output(self, model_id: bytes, input_hash: bytes, output_hash: bytes) -> tuple[bool, bytes]:
        """Verify an output (O(1) operation)."""
        return self.contract.functions.verifyOutput(model_id, input_hash, output_hash).call()

    def get_expected_output(self, model_id: bytes, input_hash: bytes) -> bytes:
        """Get expected output for a given input (O(1) operation)."""
        return self.contract.functions.getExpectedOutput(model_id, input_hash).call()
