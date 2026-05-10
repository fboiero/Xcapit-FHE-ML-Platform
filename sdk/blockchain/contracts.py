"""Smart contract wrappers for the FHE-ML platform.

Provides typed interfaces for the ModelRegistry and Governance contracts.
"""

from typing import Any

try:
    from web3 import Web3

    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False

from .connector import BlockchainConnector


class ContractBase:
    """Base class for smart-contract wrappers.

    Handles common patterns: holding a connector reference,
    instantiating the web3 contract, and providing call/transact helpers.
    """

    def __init__(
        self,
        connector: BlockchainConnector,
        address: str,
        abi: list,
    ):
        """Initialize the contract wrapper.

        Args:
            connector: Active BlockchainConnector instance.
            address: Deployed contract address.
            abi: Contract ABI (list of dicts).
        """
        self._connector = connector
        self._address = address
        self._abi = abi
        self._contract = connector.get_contract(address, abi)

    @property
    def address(self) -> str:
        """The contract address."""
        return self._address

    @property
    def connector(self) -> BlockchainConnector:
        """The underlying connector."""
        return self._connector

    def call(self, function_name: str, *args: Any) -> Any:
        """Call a read-only contract function.

        Args:
            function_name: Name of the contract function.
            *args: Positional arguments for the function.

        Returns:
            The return value from the contract call.
        """
        fn = self._contract.functions[function_name](*args)
        return fn.call()

    def transact(self, function_name: str, *args: Any) -> str:
        """Execute a state-changing contract function.

        Builds the transaction, signs it with the connector's account,
        and returns the transaction hash.

        Args:
            function_name: Name of the contract function.
            *args: Positional arguments for the function.

        Returns:
            Transaction hash as hex string.
        """
        fn = self._contract.functions[function_name](*args)
        tx = fn.build_transaction(
            {
                "from": Web3.to_checksum_address(self._connector.address),
                "nonce": self._connector.get_nonce(),
                "chainId": self._connector.config.chain_id,
                "gasPrice": self._connector.get_gas_price(),
            }
        )
        return self._connector.send_transaction(tx)


class ModelRegistryContract(ContractBase):
    """Wrapper for the on-chain Model Registry contract.

    Provides typed methods for registering, querying, updating,
    and verifying ML models on-chain.
    """

    def register_model(
        self, model_hash: str, metadata_uri: str
    ) -> str:
        """Register a new model on-chain.

        Args:
            model_hash: SHA-256 hash of the model artefact.
            metadata_uri: URI pointing to model metadata (IPFS, HTTP, etc.).

        Returns:
            Transaction hash.
        """
        return self.transact("registerModel", model_hash, metadata_uri)

    def get_model(self, model_id: int) -> dict:
        """Retrieve model information by ID.

        Args:
            model_id: On-chain model identifier.

        Returns:
            Dict with model_hash, metadata_uri, owner, timestamp, etc.
        """
        result = self.call("getModel", model_id)
        # Contract typically returns a tuple; map to dict
        if isinstance(result, (list, tuple)):
            keys = [
                "model_hash",
                "metadata_uri",
                "owner",
                "timestamp",
                "is_active",
            ]
            return dict(zip(keys, result))
        return result

    def update_model(
        self, model_id: int, new_hash: str
    ) -> str:
        """Update the hash for an existing model.

        Args:
            model_id: On-chain model identifier.
            new_hash: New SHA-256 hash.

        Returns:
            Transaction hash.
        """
        return self.transact("updateModel", model_id, new_hash)

    def list_models(self) -> list[dict]:
        """List all registered models.

        Returns:
            List of model info dicts.
        """
        count = self.call("getModelCount")
        models = []
        for i in range(count):
            try:
                model = self.get_model(i)
                model["model_id"] = i
                models.append(model)
            except Exception:
                continue
        return models

    def verify_model(self, model_id: int) -> dict:
        """Verify a model's on-chain registration.

        Args:
            model_id: On-chain model identifier.

        Returns:
            Dict with verification status and details.
        """
        model = self.get_model(model_id)
        return {
            "model_id": model_id,
            "verified": model.get("is_active", False),
            "model_hash": model.get("model_hash"),
            "owner": model.get("owner"),
            "timestamp": model.get("timestamp"),
        }


class GovernanceContract(ContractBase):
    """Wrapper for the on-chain Governance contract.

    Provides typed methods for creating proposals, voting,
    and executing governance actions.
    """

    def create_proposal(
        self, description: str, actions: list[dict]
    ) -> str:
        """Create a new governance proposal.

        Args:
            description: Human-readable proposal description.
            actions: List of action dicts (target, calldata, value).

        Returns:
            Transaction hash.
        """
        targets = [a.get("target", "") for a in actions]
        calldatas = [a.get("calldata", b"") for a in actions]
        values = [a.get("value", 0) for a in actions]
        return self.transact(
            "createProposal", description, targets, calldatas, values
        )

    def vote(self, proposal_id: int, support: bool) -> str:
        """Cast a vote on a proposal.

        Args:
            proposal_id: On-chain proposal identifier.
            support: True for in favour, False for against.

        Returns:
            Transaction hash.
        """
        return self.transact("vote", proposal_id, support)

    def execute_proposal(self, proposal_id: int) -> str:
        """Execute a passed proposal.

        Args:
            proposal_id: On-chain proposal identifier.

        Returns:
            Transaction hash.
        """
        return self.transact("executeProposal", proposal_id)

    def get_proposal(self, proposal_id: int) -> dict:
        """Retrieve proposal information.

        Args:
            proposal_id: On-chain proposal identifier.

        Returns:
            Dict with description, votes_for, votes_against, status, etc.
        """
        result = self.call("getProposal", proposal_id)
        if isinstance(result, (list, tuple)):
            keys = [
                "description",
                "proposer",
                "votes_for",
                "votes_against",
                "status",
                "created_at",
                "executed",
            ]
            return dict(zip(keys, result))
        return result
