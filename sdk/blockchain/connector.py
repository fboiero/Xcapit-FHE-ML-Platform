"""Blockchain connector for interacting with EVM-compatible networks.

Provides a high-level interface for connecting to Arbitrum and Ethereum
networks, managing accounts, and sending transactions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware

    HAS_WEB3 = True
except ImportError:
    Web3 = None
    HAS_WEB3 = False


def _require_web3():
    """Raise ImportError with installation instructions if web3 is missing."""
    if not HAS_WEB3:
        raise ImportError(
            "web3 is required for blockchain operations. "
            "Install it with: pip install web3"
        )


class Network(Enum):
    """Supported blockchain networks."""

    ARBITRUM_ONE = "arbitrum-one"
    ARBITRUM_SEPOLIA = "arbitrum-sepolia"
    ETHEREUM_MAINNET = "ethereum-mainnet"
    ETHEREUM_SEPOLIA = "ethereum-sepolia"


@dataclass
class NetworkConfig:
    """Configuration for a blockchain network.

    Attributes:
        chain_id: The network chain ID.
        rpc_url: Default JSON-RPC endpoint URL.
        explorer_url: Block explorer base URL.
        is_testnet: Whether this is a test network.
        native_currency: Symbol for the native currency (e.g. ETH).
    """

    chain_id: int
    rpc_url: str
    explorer_url: str
    is_testnet: bool
    native_currency: str


NETWORK_CONFIGS: dict[Network, NetworkConfig] = {
    Network.ARBITRUM_ONE: NetworkConfig(
        chain_id=42161,
        rpc_url="https://arb1.arbitrum.io/rpc",
        explorer_url="https://arbiscan.io",
        is_testnet=False,
        native_currency="ETH",
    ),
    Network.ARBITRUM_SEPOLIA: NetworkConfig(
        chain_id=421614,
        rpc_url="https://sepolia-rollup.arbitrum.io/rpc",
        explorer_url="https://sepolia.arbiscan.io",
        is_testnet=True,
        native_currency="ETH",
    ),
    Network.ETHEREUM_MAINNET: NetworkConfig(
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        explorer_url="https://etherscan.io",
        is_testnet=False,
        native_currency="ETH",
    ),
    Network.ETHEREUM_SEPOLIA: NetworkConfig(
        chain_id=11155111,
        rpc_url="https://rpc.sepolia.org",
        explorer_url="https://sepolia.etherscan.io",
        is_testnet=True,
        native_currency="ETH",
    ),
}


class BlockchainConnector:
    """High-level connector for EVM-compatible blockchain networks.

    Manages RPC connections, accounts, and transaction lifecycle.

    Example:
        >>> from sdk.blockchain import BlockchainConnector, Network
        >>> connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        >>> connector.set_account(private_key)
        >>> connector.connect()
        >>> balance = connector.get_balance_eth(connector.address)
    """

    def __init__(
        self,
        network: Union[Network, str],
        rpc_url: Optional[str] = None,
    ):
        """Initialize the connector.

        Args:
            network: Target network (Network enum or string value).
            rpc_url: Custom RPC URL. If None, uses the default for the network.
        """
        _require_web3()

        if isinstance(network, str):
            try:
                network = Network(network)
            except ValueError:
                # Try matching by name
                for n in Network:
                    if n.value == network or n.name.lower() == network.lower():
                        network = n
                        break
                else:
                    raise ValueError(
                        f"Unknown network: {network}. "
                        f"Valid options: {[n.value for n in Network]}"
                    )

        self._network = network
        self._config = NETWORK_CONFIGS[network]
        self._rpc_url = rpc_url or self._config.rpc_url
        self._web3: Optional[Web3] = None
        self._account = None
        self._connected = False

    @property
    def network(self) -> Network:
        """The target network."""
        return self._network

    @property
    def config(self) -> NetworkConfig:
        """Network configuration."""
        return self._config

    @property
    def web3(self) -> Web3:
        """The Web3 instance. Raises if not connected."""
        if self._web3 is None:
            raise ConnectionError(
                "Not connected. Call connect() first."
            )
        return self._web3

    @property
    def account(self):
        """The active account. None if no account is set."""
        return self._account

    @property
    def address(self) -> Optional[str]:
        """The active account address, or None."""
        if self._account is None:
            return None
        return self._account.address

    @property
    def is_connected(self) -> bool:
        """Whether the connector has an active RPC connection."""
        if self._web3 is None:
            return False
        try:
            return self._web3.is_connected()
        except Exception:
            return False

    def connect(self) -> BlockchainConnector:
        """Establish connection to the RPC endpoint.

        Returns:
            self, for method chaining.

        Raises:
            ConnectionError: If the RPC endpoint is unreachable.
        """
        self._web3 = Web3(Web3.HTTPProvider(self._rpc_url))

        # Inject POA middleware for Arbitrum / L2 chains
        if self._config.chain_id in (42161, 421614):
            try:
                self._web3.middleware_onion.inject(
                    ExtraDataToPOAMiddleware, layer=0
                )
            except Exception:
                pass  # Middleware may already be injected

        if not self._web3.is_connected():
            raise ConnectionError(
                f"Failed to connect to {self._rpc_url}"
            )

        self._connected = True
        return self

    def disconnect(self) -> None:
        """Close the RPC connection."""
        self._web3 = None
        self._connected = False

    def set_account(self, private_key: str) -> BlockchainConnector:
        """Set the active account from a private key.

        Args:
            private_key: Hex-encoded private key (with or without 0x prefix).

        Returns:
            self, for method chaining.
        """
        _require_web3()
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        self._account = Web3().eth.account.from_key(private_key)
        return self

    def set_account_from_keyfile(
        self, keyfile_path: str, password: str
    ) -> BlockchainConnector:
        """Set the active account from an encrypted keyfile.

        Args:
            keyfile_path: Path to the JSON keyfile.
            password: Password to decrypt the keyfile.

        Returns:
            self, for method chaining.
        """
        _require_web3()
        with open(keyfile_path) as f:
            keyfile_json = json.load(f)
        private_key = Web3().eth.account.decrypt(keyfile_json, password)
        self._account = Web3().eth.account.from_key(private_key)
        return self

    def get_balance(self, address: Optional[str] = None) -> int:
        """Get balance in wei.

        Args:
            address: Address to query. Defaults to the active account.

        Returns:
            Balance in wei.
        """
        address = address or self.address
        if address is None:
            raise ValueError("No address provided and no account set.")
        return self.web3.eth.get_balance(
            Web3.to_checksum_address(address)
        )

    def get_balance_eth(self, address: Optional[str] = None) -> float:
        """Get balance in ETH.

        Args:
            address: Address to query. Defaults to the active account.

        Returns:
            Balance in ETH as a float.
        """
        wei = self.get_balance(address)
        return float(Web3.from_wei(wei, "ether"))

    def get_nonce(self, address: Optional[str] = None) -> int:
        """Get the transaction count (nonce) for an address.

        Args:
            address: Address to query. Defaults to the active account.

        Returns:
            Current nonce.
        """
        address = address or self.address
        if address is None:
            raise ValueError("No address provided and no account set.")
        return self.web3.eth.get_transaction_count(
            Web3.to_checksum_address(address)
        )

    def estimate_gas(
        self,
        transaction: dict,
        buffer_percent: int = 10,
    ) -> int:
        """Estimate gas for a transaction with an optional buffer.

        Args:
            transaction: Transaction dict (to, data, value, etc.).
            buffer_percent: Percentage buffer to add on top of estimate.

        Returns:
            Estimated gas with buffer applied.
        """
        estimate = self.web3.eth.estimate_gas(transaction)
        return int(estimate * (1 + buffer_percent / 100))

    def get_gas_price(self) -> int:
        """Get current gas price in wei.

        Returns:
            Gas price in wei.
        """
        return self.web3.eth.gas_price

    def send_transaction(self, transaction: dict) -> str:
        """Sign and send a transaction.

        Args:
            transaction: Transaction dict. Fields like nonce, gas, gasPrice,
                and chainId are filled automatically if missing.

        Returns:
            Transaction hash as hex string.

        Raises:
            ValueError: If no account is set.
        """
        if self._account is None:
            raise ValueError(
                "No account set. Call set_account() first."
            )

        address = self.address
        checksum = Web3.to_checksum_address(address)

        # Fill defaults
        if "nonce" not in transaction:
            transaction["nonce"] = self.get_nonce(address)
        if "chainId" not in transaction:
            transaction["chainId"] = self._config.chain_id
        if "gasPrice" not in transaction and "maxFeePerGas" not in transaction:
            transaction["gasPrice"] = self.get_gas_price()
        if "gas" not in transaction:
            transaction["gas"] = self.estimate_gas(transaction)
        if "from" not in transaction:
            transaction["from"] = checksum

        signed = self._account.sign_transaction(transaction)
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    def wait_for_transaction(
        self,
        tx_hash: str,
        timeout: int = 120,
    ) -> dict:
        """Wait for a transaction to be mined and return its receipt.

        Args:
            tx_hash: Transaction hash.
            timeout: Maximum seconds to wait.

        Returns:
            Transaction receipt as a dict.
        """
        receipt = self.web3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=timeout
        )
        return dict(receipt)

    def deploy_contract(
        self,
        abi: list,
        bytecode: str,
        constructor_args: Optional[list] = None,
    ) -> dict:
        """Deploy a smart contract.

        Args:
            abi: Contract ABI.
            bytecode: Contract bytecode.
            constructor_args: Arguments for the constructor.

        Returns:
            Dict with 'address' and 'tx_hash'.
        """
        if self._account is None:
            raise ValueError("No account set. Call set_account() first.")

        contract = self.web3.eth.contract(abi=abi, bytecode=bytecode)

        args = constructor_args or []
        tx = contract.constructor(*args).build_transaction(
            {
                "from": Web3.to_checksum_address(self.address),
                "nonce": self.get_nonce(),
                "chainId": self._config.chain_id,
                "gasPrice": self.get_gas_price(),
            }
        )

        tx_hash = self.send_transaction(tx)
        receipt = self.wait_for_transaction(tx_hash)

        return {
            "address": receipt.get("contractAddress"),
            "tx_hash": tx_hash,
        }

    def get_contract(self, address: str, abi: list):
        """Get a contract instance for an already-deployed contract.

        Args:
            address: Contract address.
            abi: Contract ABI.

        Returns:
            web3 Contract instance.
        """
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi,
        )

    def get_explorer_url(self, tx_hash: str) -> str:
        """Build a block-explorer URL for a transaction.

        Args:
            tx_hash: Transaction hash.

        Returns:
            Full URL to the transaction on the explorer.
        """
        return f"{self._config.explorer_url}/tx/{tx_hash}"

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        addr = self.address or "no account"
        return (
            f"BlockchainConnector("
            f"network={self._network.value}, "
            f"status={status}, "
            f"address={addr})"
        )
