"""Blockchain commands: connect, register, checkpoint, verify."""

import pickle
from pathlib import Path

import numpy as np


def cmd_blockchain_connect(args) -> int:
    """Test blockchain connection."""
    from ...blockchain import BlockchainConnector, Network

    network_map = {
        "arbitrum": Network.ARBITRUM_ONE,
        "arbitrum-sepolia": Network.ARBITRUM_SEPOLIA,
        "ethereum": Network.ETHEREUM_MAINNET,
        "ethereum-sepolia": Network.ETHEREUM_SEPOLIA,
        "local": Network.LOCAL,
    }

    network = network_map.get(args.network, Network.ARBITRUM_SEPOLIA)
    print(f"Connecting to {network.value}...")

    connector = BlockchainConnector(network, rpc_url=args.rpc)

    try:
        connector.connect()
        print(f"  Connected!")
        print(f"  Chain ID: {connector.config.chain_id}")
        print(f"  RPC: {connector._rpc_url}")

        if args.private_key:
            address = connector.set_account(args.private_key)
            balance = connector.get_balance_eth()
            print(f"  Address: {address}")
            print(f"  Balance: {balance:.6f} ETH")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_blockchain_register(args) -> int:
    """Register a model on blockchain."""
    from ...blockchain import BlockchainConnector, Network, ModelRegistryClient

    network_map = {
        "arbitrum": Network.ARBITRUM_ONE,
        "arbitrum-sepolia": Network.ARBITRUM_SEPOLIA,
        "local": Network.LOCAL,
    }

    network = network_map.get(args.network, Network.ARBITRUM_SEPOLIA)

    print(f"Registering model on {network.value}...")

    # Load model to get type
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: Model file not found: {model_path}")
        return 1

    with open(model_path, "rb") as f:
        model_bundle = pickle.load(f)

    model_type = model_bundle.get("model_type", "unknown")
    version = args.version or model_bundle.get("version", "1.0.0")

    print(f"  Model type: {model_type}")
    print(f"  Version: {version}")

    # Connect to blockchain
    connector = BlockchainConnector(network, rpc_url=args.rpc)
    connector.connect()
    connector.set_account(args.private_key)

    balance = connector.get_balance_eth()
    print(f"  Account: {connector.address}")
    print(f"  Balance: {balance:.6f} ETH")

    if balance < 0.001:
        print("Error: Insufficient balance for gas fees")
        return 1

    # Register model
    registry = ModelRegistryClient(connector, args.contract)
    print(f"\n  Registering on contract: {args.contract[:12]}...")

    try:
        tx_hash = registry.register_model(model_type, version)
        print(f"\n  Transaction: {tx_hash}")
        print(f"  Explorer: {connector.get_explorer_url(tx_hash)}")
        print("\n  Model registered successfully!")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_blockchain_checkpoint(args) -> int:
    """Save a training checkpoint to blockchain."""
    from ...blockchain import BlockchainConnector, Network, ModelRegistryClient

    network_map = {
        "arbitrum": Network.ARBITRUM_ONE,
        "arbitrum-sepolia": Network.ARBITRUM_SEPOLIA,
        "local": Network.LOCAL,
    }

    network = network_map.get(args.network, Network.ARBITRUM_SEPOLIA)

    print(f"Saving checkpoint to {network.value}...")

    # Load model weights
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: Model file not found: {model_path}")
        return 1

    with open(model_path, "rb") as f:
        model_bundle = pickle.load(f)

    params = model_bundle.get("params", {})
    weights = params.get("weights")
    if weights is None:
        print("Error: Model has no weights to checkpoint")
        return 1

    weights_array = np.array(weights)
    print(f"  Weights shape: {weights_array.shape}")

    # Connect and save checkpoint
    connector = BlockchainConnector(network, rpc_url=args.rpc)
    connector.connect()
    connector.set_account(args.private_key)

    registry = ModelRegistryClient(connector, args.contract)

    metrics = {"epoch": args.epoch}
    if params.get("bias"):
        metrics["bias"] = params["bias"]

    print(f"  Model ID: {args.model_id}")
    print(f"  Epoch: {args.epoch}")

    try:
        tx_hash = registry.save_checkpoint(
            args.model_id,
            args.epoch,
            weights_array,
            metrics,
        )
        print(f"\n  Transaction: {tx_hash}")
        print(f"  Explorer: {connector.get_explorer_url(tx_hash)}")
        print("\n  Checkpoint saved!")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_blockchain_verify(args) -> int:
    """Verify a model checkpoint on blockchain."""
    from ...blockchain import BlockchainConnector, Network, ModelRegistryClient

    network_map = {
        "arbitrum": Network.ARBITRUM_ONE,
        "arbitrum-sepolia": Network.ARBITRUM_SEPOLIA,
        "local": Network.LOCAL,
    }

    network = network_map.get(args.network, Network.ARBITRUM_SEPOLIA)

    print(f"Verifying model on {network.value}...")

    # Connect (read-only, no private key needed)
    connector = BlockchainConnector(network, rpc_url=args.rpc)
    connector.connect()

    registry = ModelRegistryClient(connector, args.contract)

    # Get model info
    print(f"  Model ID: {args.model_id}")

    try:
        model_info = registry.get_model(args.model_id)
        print(f"\n  Owner: {model_info.owner}")
        print(f"  Type: {model_info.model_type}")
        print(f"  Version: {model_info.version}")
        print(f"  Verified: {model_info.verified}")
        print(f"  Active: {model_info.active}")
        print(f"  Created: {model_info.created_at}")
        print(f"  Updated: {model_info.updated_at}")

        # Get checkpoints
        checkpoint_count = registry.get_checkpoint_count(args.model_id)
        print(f"\n  Checkpoints: {checkpoint_count}")

        if checkpoint_count > 0:
            print("\n  Recent checkpoints:")
            for i in range(min(5, checkpoint_count)):
                cp = registry.get_checkpoint(args.model_id, i)
                print(f"    [{i}] Epoch {cp.epoch}: {cp.weights_hash[:16]}... ({cp.timestamp})")

        # Verify local model if provided
        if args.model:
            model_path = Path(args.model)
            if model_path.exists():
                with open(model_path, "rb") as f:
                    model_bundle = pickle.load(f)

                params = model_bundle.get("params", {})
                weights = params.get("weights")

                if weights:
                    weights_array = np.array(weights)
                    is_valid = registry.verify_checkpoint(
                        args.model_id,
                        args.epoch or 0,
                        weights_array,
                    )
                    print(f"\n  Local model valid: {is_valid}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


__all__ = [
    "cmd_blockchain_connect",
    "cmd_blockchain_register",
    "cmd_blockchain_checkpoint",
    "cmd_blockchain_verify",
]
