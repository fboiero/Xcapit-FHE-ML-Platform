"""Blockchain network connector.

This module provides connection management for EVM-compatible blockchains,
with primary support for Arbitrum.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

# Support both web3 v5 and v6+ middleware imports
try:
    from web3.middleware import ExtraDataToPOAMiddleware
except ImportError:
    from web3.middleware import geth_poa_middleware as ExtraDataToPOAMiddleware


class Network(Enum):
    """Supported blockchain networks."""

    # Arbitrum
    ARBITRUM_ONE = "arbitrum-one"
    ARBITRUM_SEPOLIA = "arbitrum-sepolia"  # Testnet

    # Ethereum (for testing/comparison)
    ETHEREUM_MAINNET = "ethereum-mainnet"
    ETHEREUM_SEPOLIA = "ethereum-sepolia"

    # Local development
    LOCAL = "local"


@dataclass
class NetworkConfig:
    """Configuration for a blockchain network."""

    name: str
    chain_id: int
    rpc_url: str
    explorer_url: str
    is_testnet: bool
    native_currency: str = "ETH"


# Network configurations
NETWORK_CONFIGS: dict[Network, NetworkConfig] = {
    Network.ARBITRUM_ONE: NetworkConfig(
        name="Arbitrum One",
        chain_id=42161,
        rpc_url="https://arb1.arbitrum.io/rpc",
        explorer_url="https://arbiscan.io",
        is_testnet=False,
    ),
    Network.ARBITRUM_SEPOLIA: NetworkConfig(
        name="Arbitrum Sepolia",
        chain_id=421614,
        rpc_url="https://sepolia-rollup.arbitrum.io/rpc",
        explorer_url="https://sepolia.arbiscan.io",
        is_testnet=True,
    ),
    Network.ETHEREUM_MAINNET: NetworkConfig(
        name="Ethereum Mainnet",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        explorer_url="https://etherscan.io",
        is_testnet=False,
    ),
    Network.ETHEREUM_SEPOLIA: NetworkConfig(
        name="Ethereum Sepolia",
        chain_id=11155111,
        rpc_url="https://rpc.sepolia.org",
        explorer_url="https://sepolia.etherscan.io",
        is_testnet=True,
    ),
    Network.LOCAL: NetworkConfig(
        name="Local Development",
        chain_id=31337,
        rpc_url="http://127.0.0.1:8545",
        explorer_url="",
        is_testnet=True,
    ),
}


class BlockchainConnector:
    """Manages connection to EVM-compatible blockchains.

    This class handles:
    - Network connection and configuration
    - Account management
    - Transaction signing and sending
    - Contract deployment and interaction

    Example:
        >>> connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        >>> connector.set_account(private_key)
        >>> connector.connect()
        >>> tx_hash = connector.send_transaction(...)
    """

    def __init__(
        self,
        network: Network = Network.ARBITRUM_SEPOLIA,
        rpc_url: Optional[str] = None,
    ):
        """Initialize blockchain connector.

        Args:
            network: Target network.
            rpc_url: Custom RPC URL (overrides default).
        """
        self._network = network
        self._config = NETWORK_CONFIGS[network]
        self._rpc_url = rpc_url or self._config.rpc_url
        self._web3: Optional[Web3] = None
        self._account: Optional[LocalAccount] = None
        self._connected = False

    @property
    def network(self) -> Network:
        """Get current network."""
        return self._network

    @property
    def config(self) -> NetworkConfig:
        """Get network configuration."""
        return self._config

    @property
    def web3(self) -> Web3:
        """Get Web3 instance."""
        if self._web3 is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._web3

    @property
    def account(self) -> Optional[LocalAccount]:
        """Get current account."""
        return self._account

    @property
    def address(self) -> Optional[str]:
        """Get current account address."""
        return self._account.address if self._account else None

    @property
    def is_connected(self) -> bool:
        """Check if connected to network."""
        return self._connected and self._web3 is not None

    def connect(self) -> bool:
        """Connect to the blockchain network.

        Returns:
            True if connection successful.

        Raises:
            ConnectionError: If connection fails.
        """
        try:
            self._web3 = Web3(Web3.HTTPProvider(self._rpc_url))

            # Add middleware for POA chains (Arbitrum)
            self._web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            # Verify connection
            if not self._web3.is_connected():
                raise ConnectionError(f"Failed to connect to {self._rpc_url}")

            # Verify chain ID
            chain_id = self._web3.eth.chain_id
            if chain_id != self._config.chain_id:
                raise ConnectionError(
                    f"Chain ID mismatch. Expected {self._config.chain_id}, got {chain_id}"
                )

            self._connected = True
            return True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Connection failed: {e}")

    def disconnect(self) -> None:
        """Disconnect from the network."""
        self._web3 = None
        self._connected = False

    def set_account(self, private_key: str) -> str:
        """Set the account for signing transactions.

        Args:
            private_key: Private key (hex string, with or without 0x prefix).

        Returns:
            Account address.
        """
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        self._account = Account.from_key(private_key)
        return self._account.address

    def set_account_from_keyfile(
        self,
        keyfile_path: str,
        password: str,
    ) -> str:
        """Set account from encrypted keyfile.

        Args:
            keyfile_path: Path to keyfile JSON.
            password: Password to decrypt keyfile.

        Returns:
            Account address.
        """
        with open(keyfile_path) as f:
            keyfile = json.load(f)

        private_key = Account.decrypt(keyfile, password)
        return self.set_account(private_key.hex())

    def get_balance(self, address: Optional[str] = None) -> int:
        """Get account balance in wei.

        Args:
            address: Address to check. Uses current account if None.

        Returns:
            Balance in wei.
        """
        if address is None:
            if self._account is None:
                raise ValueError("No address specified and no account set")
            address = self._account.address

        return self.web3.eth.get_balance(address)

    def get_balance_eth(self, address: Optional[str] = None) -> float:
        """Get account balance in ETH.

        Args:
            address: Address to check. Uses current account if None.

        Returns:
            Balance in ETH.
        """
        wei = self.get_balance(address)
        return float(Web3.from_wei(wei, "ether"))

    def get_nonce(self, address: Optional[str] = None) -> int:
        """Get transaction nonce for address.

        Args:
            address: Address to check. Uses current account if None.

        Returns:
            Current nonce.
        """
        if address is None:
            if self._account is None:
                raise ValueError("No address specified and no account set")
            address = self._account.address

        return self.web3.eth.get_transaction_count(address)

    def estimate_gas(self, transaction: dict[str, Any]) -> int:
        """Estimate gas for a transaction.

        Args:
            transaction: Transaction dictionary.

        Returns:
            Estimated gas units.
        """
        return self.web3.eth.estimate_gas(transaction)

    def get_gas_price(self, buffer_percent: int = 20) -> int:
        """Get current gas price in wei with buffer for fluctuations.

        Args:
            buffer_percent: Percentage buffer to add (default 20%).

        Returns:
            Gas price in wei with buffer.
        """
        base_price = self.web3.eth.gas_price
        # Add buffer to handle base fee fluctuations
        return int(base_price * (100 + buffer_percent) / 100)

    def send_transaction(
        self,
        to: str,
        value: int = 0,
        data: bytes = b"",
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        nonce: Optional[int] = None,
    ) -> str:
        """Send a signed transaction.

        Args:
            to: Recipient address.
            value: Value in wei.
            data: Transaction data.
            gas: Gas limit (estimated if None).
            gas_price: Gas price (uses network default if None).
            nonce: Transaction nonce (fetched if None).

        Returns:
            Transaction hash.

        Raises:
            ValueError: If no account is set.
        """
        if self._account is None:
            raise ValueError("No account set. Call set_account() first.")

        # Build transaction
        tx = {
            "from": self._account.address,
            "to": to,
            "value": value,
            "data": data,
            "chainId": self._config.chain_id,
            "nonce": nonce or self.get_nonce(),
        }

        # Estimate gas if not provided
        if gas is None:
            tx["gas"] = self.estimate_gas(tx)
        else:
            tx["gas"] = gas

        # Set gas price
        if gas_price is None:
            tx["gasPrice"] = self.get_gas_price()
        else:
            tx["gasPrice"] = gas_price

        # Sign transaction
        signed = self._account.sign_transaction(tx)

        # Send transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)

        return tx_hash.hex()

    def wait_for_transaction(
        self,
        tx_hash: str,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Wait for transaction confirmation.

        Args:
            tx_hash: Transaction hash.
            timeout: Timeout in seconds.

        Returns:
            Transaction receipt.
        """
        receipt = self.web3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=timeout,
        )
        return dict(receipt)

    def deploy_contract(
        self,
        abi: list,
        bytecode: str,
        constructor_args: tuple = (),
        gas: Optional[int] = None,
    ) -> tuple:
        """Deploy a smart contract.

        Args:
            abi: Contract ABI.
            bytecode: Contract bytecode.
            constructor_args: Constructor arguments.
            gas: Gas limit.

        Returns:
            Tuple of (contract_address, tx_hash).
        """
        if self._account is None:
            raise ValueError("No account set. Call set_account() first.")

        contract = self.web3.eth.contract(abi=abi, bytecode=bytecode)

        # Get gas price with 20% buffer for network fluctuations
        base_gas_price = self.get_gas_price()
        gas_price_with_buffer = int(base_gas_price * 1.2)

        # Build deployment transaction
        tx = contract.constructor(*constructor_args).build_transaction(
            {
                "from": self._account.address,
                "nonce": self.get_nonce(),
                "gas": gas or 3000000,
                "gasPrice": gas_price_with_buffer,
                "chainId": self._config.chain_id,
            }
        )

        # Sign and send
        signed = self._account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)

        # Wait for deployment
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return receipt.contractAddress, tx_hash.hex()

    def get_contract(self, address: str, abi: list):
        """Get a contract instance.

        Args:
            address: Contract address.
            abi: Contract ABI.

        Returns:
            Web3 contract instance.
        """
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi,
        )

    def get_explorer_url(self, tx_hash: str) -> str:
        """Get block explorer URL for a transaction.

        Args:
            tx_hash: Transaction hash.

        Returns:
            Explorer URL.
        """
        if not self._config.explorer_url:
            return ""
        return f"{self._config.explorer_url}/tx/{tx_hash}"

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        addr = self.address[:10] + "..." if self.address else "no account"
        return f"BlockchainConnector({self._config.name}, {status}, {addr})"
