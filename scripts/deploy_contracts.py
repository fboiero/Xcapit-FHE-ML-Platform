#!/usr/bin/env python3
"""Deploy FHE-ML smart contracts to Arbitrum.

This script compiles and deploys the ModelRegistry and ComputationVerifier
contracts to Arbitrum Sepolia (testnet) or Arbitrum One (mainnet).

Usage:
    python scripts/deploy_contracts.py --network arbitrum-sepolia
    python scripts/deploy_contracts.py --network arbitrum-one --verify
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import solcx
    from solcx import compile_source, install_solc
except ImportError:
    print("Error: py-solc-x not installed. Run: pip install py-solc-x")
    sys.exit(1)

from sdk.blockchain import BlockchainConnector, Network, NETWORK_CONFIGS


# Constants
CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
DEPLOYMENTS_DIR = Path(__file__).parent.parent / "deployments"
SOLC_VERSION = "0.8.20"


def ensure_solc() -> None:
    """Ensure the required Solidity compiler is installed."""
    try:
        installed = solcx.get_installed_solc_versions()
        if SOLC_VERSION not in [str(v) for v in installed]:
            print(f"Installing Solidity compiler {SOLC_VERSION}...")
            install_solc(SOLC_VERSION)
        solcx.set_solc_version(SOLC_VERSION)
    except Exception as e:
        print(f"Error setting up Solidity compiler: {e}")
        sys.exit(1)


def compile_contract(contract_name: str) -> Tuple[list, str]:
    """Compile a Solidity contract.

    Args:
        contract_name: Name of the contract file (without .sol).

    Returns:
        Tuple of (abi, bytecode).
    """
    contract_path = CONTRACTS_DIR / f"{contract_name}.sol"

    if not contract_path.exists():
        raise FileNotFoundError(f"Contract not found: {contract_path}")

    with open(contract_path, "r") as f:
        source = f.read()

    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=SOLC_VERSION,
    )

    # Get the main contract
    contract_key = f"<stdin>:{contract_name}"
    if contract_key not in compiled:
        # Try to find the contract in compiled output
        for key in compiled:
            if contract_name in key:
                contract_key = key
                break

    contract_data = compiled[contract_key]
    return contract_data["abi"], contract_data["bin"]


def deploy_contract(
    connector: BlockchainConnector,
    name: str,
    abi: list,
    bytecode: str,
    constructor_args: tuple = (),
) -> Tuple[str, str]:
    """Deploy a contract and return address and tx hash.

    Args:
        connector: Blockchain connector.
        name: Contract name for logging.
        abi: Contract ABI.
        bytecode: Contract bytecode.
        constructor_args: Constructor arguments.

    Returns:
        Tuple of (address, tx_hash).
    """
    print(f"\nDeploying {name}...")

    # Estimate gas
    contract = connector.web3.eth.contract(abi=abi, bytecode=bytecode)
    gas_estimate = contract.constructor(*constructor_args).estimate_gas({
        "from": connector.address,
    })
    print(f"  Estimated gas: {gas_estimate:,}")

    # Deploy
    address, tx_hash = connector.deploy_contract(
        abi=abi,
        bytecode=bytecode,
        constructor_args=constructor_args,
        gas=int(gas_estimate * 1.2),  # 20% buffer
    )

    print(f"  Contract deployed at: {address}")
    print(f"  Transaction hash: {tx_hash}")

    if connector.config.explorer_url:
        print(f"  Explorer: {connector.get_explorer_url(tx_hash)}")

    return address, tx_hash


def save_deployment(
    network: Network,
    contracts: Dict[str, Dict],
    deployer: str,
) -> Path:
    """Save deployment info to JSON file.

    Args:
        network: Network where contracts were deployed.
        contracts: Contract deployment info.
        deployer: Deployer address.

    Returns:
        Path to deployment file.
    """
    DEPLOYMENTS_DIR.mkdir(exist_ok=True)

    deployment = {
        "network": network.value,
        "chainId": NETWORK_CONFIGS[network].chain_id,
        "deployer": deployer,
        "deployedAt": datetime.utcnow().isoformat(),
        "contracts": contracts,
    }

    filename = f"{network.value}.json"
    filepath = DEPLOYMENTS_DIR / filename

    with open(filepath, "w") as f:
        json.dump(deployment, f, indent=2)

    print(f"\nDeployment saved to: {filepath}")
    return filepath


def save_abis(contracts: Dict[str, Dict]) -> None:
    """Save contract ABIs for SDK use.

    Args:
        contracts: Contract info with ABIs.
    """
    abi_dir = DEPLOYMENTS_DIR / "abis"
    abi_dir.mkdir(exist_ok=True)

    for name, info in contracts.items():
        abi_path = abi_dir / f"{name}.json"
        with open(abi_path, "w") as f:
            json.dump(info["abi"], f, indent=2)
        print(f"  Saved ABI: {abi_path}")


def get_private_key() -> str:
    """Get private key from environment or prompt.

    Returns:
        Private key string.
    """
    key = os.environ.get("DEPLOYER_PRIVATE_KEY")
    if not key:
        key = os.environ.get("PRIVATE_KEY")
    if not key:
        print("\nPrivate key not found in environment.")
        print("Set DEPLOYER_PRIVATE_KEY or PRIVATE_KEY environment variable.")
        sys.exit(1)
    return key


def parse_network(network_str: str) -> Network:
    """Parse network string to Network enum.

    Args:
        network_str: Network name string.

    Returns:
        Network enum value.
    """
    network_map = {
        "arbitrum-one": Network.ARBITRUM_ONE,
        "arbitrum-sepolia": Network.ARBITRUM_SEPOLIA,
        "ethereum-mainnet": Network.ETHEREUM_MAINNET,
        "ethereum-sepolia": Network.ETHEREUM_SEPOLIA,
        "local": Network.LOCAL,
    }

    if network_str not in network_map:
        print(f"Unknown network: {network_str}")
        print(f"Available networks: {list(network_map.keys())}")
        sys.exit(1)

    return network_map[network_str]


def main():
    parser = argparse.ArgumentParser(
        description="Deploy FHE-ML smart contracts to blockchain"
    )
    parser.add_argument(
        "--network",
        type=str,
        default="arbitrum-sepolia",
        help="Target network (default: arbitrum-sepolia)",
    )
    parser.add_argument(
        "--rpc-url",
        type=str,
        help="Custom RPC URL (optional)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Print verification commands for block explorer",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile only, don't deploy",
    )

    args = parser.parse_args()
    network = parse_network(args.network)

    print("=" * 60)
    print("Xcapit FHE-ML Platform - Contract Deployment")
    print("=" * 60)
    print(f"\nTarget network: {NETWORK_CONFIGS[network].name}")
    print(f"Chain ID: {NETWORK_CONFIGS[network].chain_id}")

    if not NETWORK_CONFIGS[network].is_testnet:
        print("\n⚠️  WARNING: Deploying to MAINNET!")
        response = input("Type 'yes' to confirm: ")
        if response.lower() != "yes":
            print("Deployment cancelled.")
            sys.exit(0)

    # Ensure Solidity compiler
    print("\nSetting up Solidity compiler...")
    ensure_solc()
    print(f"  Using solc {SOLC_VERSION}")

    # Compile contracts
    print("\nCompiling contracts...")
    contracts_to_deploy = ["ModelRegistry", "ComputationVerifier"]
    compiled = {}

    for name in contracts_to_deploy:
        print(f"  Compiling {name}...")
        abi, bytecode = compile_contract(name)
        compiled[name] = {"abi": abi, "bytecode": bytecode}
        print(f"    ABI functions: {len(abi)}")
        print(f"    Bytecode size: {len(bytecode) // 2} bytes")

    if args.dry_run:
        print("\n[Dry run] Compilation successful. Skipping deployment.")
        return

    # Get deployer account
    private_key = get_private_key()

    # Connect to network
    print(f"\nConnecting to {NETWORK_CONFIGS[network].name}...")
    connector = BlockchainConnector(network, rpc_url=args.rpc_url)
    connector.set_account(private_key)
    connector.connect()

    print(f"  Connected: {connector.is_connected}")
    print(f"  Deployer: {connector.address}")

    balance = connector.get_balance_eth()
    print(f"  Balance: {balance:.6f} ETH")

    if balance < 0.01:
        print("\n⚠️  WARNING: Low balance. Deployment may fail.")
        if not NETWORK_CONFIGS[network].is_testnet:
            sys.exit(1)

    # Deploy contracts
    deployments = {}

    for name, data in compiled.items():
        address, tx_hash = deploy_contract(
            connector=connector,
            name=name,
            abi=data["abi"],
            bytecode=data["bytecode"],
        )
        deployments[name] = {
            "address": address,
            "transactionHash": tx_hash,
            "abi": data["abi"],
        }

    # Save deployment info
    save_deployment(network, deployments, connector.address)

    # Save ABIs
    print("\nSaving ABIs...")
    save_abis(deployments)

    # Print verification commands
    if args.verify and NETWORK_CONFIGS[network].explorer_url:
        print("\n" + "=" * 60)
        print("Contract Verification")
        print("=" * 60)
        print("\nTo verify contracts on block explorer, run:")
        for name, info in deployments.items():
            source_path = CONTRACTS_DIR / f"{name}.sol"
            print(f"\n# {name}")
            print(f"# Address: {info['address']}")
            print(f"# Source: {source_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Deployment Summary")
    print("=" * 60)
    for name, info in deployments.items():
        print(f"\n{name}:")
        print(f"  Address: {info['address']}")
        if NETWORK_CONFIGS[network].explorer_url:
            print(f"  Explorer: {NETWORK_CONFIGS[network].explorer_url}/address/{info['address']}")

    print("\n✅ Deployment complete!")


if __name__ == "__main__":
    main()
