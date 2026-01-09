"""Xcapit FHE-ML SDK Command Line Interface.

Provides CLI commands for:
- Encrypting/decrypting data
- Training models on encrypted data
- Making predictions
- Managing encryption keys
- Interacting with blockchain

Usage:
    xcapit-fhe init -o ./workspace
    xcapit-fhe encrypt --input data.csv --output encrypted.bin --target price
    xcapit-fhe train --model linear-regression --data encrypted.bin --output model.bin
    xcapit-fhe predict --model model.bin --input encrypted.bin
    xcapit-fhe decrypt --input encrypted.bin --output decrypted.csv
"""

import argparse
import os
import sys

from .utils import get_version
from .commands import (
    cmd_init,
    cmd_encrypt,
    cmd_decrypt,
    cmd_train,
    cmd_predict,
    cmd_blockchain_connect,
    cmd_blockchain_register,
    cmd_blockchain_checkpoint,
    cmd_blockchain_verify,
    cmd_api_key_create,
    cmd_api_key_list,
    cmd_api_key_revoke,
    cmd_benchmark,
    cmd_version,
    cmd_info,
)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="xcapit-fhe",
        description="Xcapit FHE-ML SDK - Privacy-preserving machine learning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  xcapit-fhe init -o ./workspace
  xcapit-fhe encrypt -i data.csv -o encrypted.bin -t target_column
  xcapit-fhe train -m linear-regression -d encrypted.bin -o model.bin
  xcapit-fhe predict -m model.bin -i encrypted.bin -o predictions.csv
  xcapit-fhe info model.bin
  xcapit-fhe benchmark --poly-degree 8192
        """
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show version",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize FHE context and keys",
    )
    init_parser.add_argument(
        "-o", "--output",
        default="./fhe_workspace",
        help="Output directory (default: ./fhe_workspace)",
    )
    init_parser.add_argument(
        "--poly-degree",
        type=int,
        default=8192,
        choices=[4096, 8192, 16384, 32768],
        help="Polynomial modulus degree (default: 8192)",
    )
    init_parser.add_argument(
        "--security",
        default="128",
        choices=["128", "192", "256"],
        help="Security level in bits (default: 128)",
    )
    init_parser.set_defaults(func=cmd_init)

    # encrypt command
    encrypt_parser = subparsers.add_parser(
        "encrypt",
        help="Encrypt data from CSV",
    )
    encrypt_parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input CSV file",
    )
    encrypt_parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output encrypted file",
    )
    encrypt_parser.add_argument(
        "-k", "--keys",
        default="./fhe_workspace/keys",
        help="Keys directory",
    )
    encrypt_parser.add_argument(
        "-t", "--target",
        help="Target column name (for supervised learning)",
    )
    encrypt_parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable data normalization",
    )
    encrypt_parser.set_defaults(func=cmd_encrypt)

    # decrypt command
    decrypt_parser = subparsers.add_parser(
        "decrypt",
        help="Decrypt encrypted data back to CSV",
    )
    decrypt_parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input encrypted file",
    )
    decrypt_parser.add_argument(
        "-o", "--output",
        help="Output CSV file (prints to stdout if not specified)",
    )
    decrypt_parser.add_argument(
        "-k", "--keys",
        help="Keys directory (uses stored path if not specified)",
    )
    decrypt_parser.add_argument(
        "--no-denormalize",
        action="store_true",
        help="Don't reverse normalization",
    )
    decrypt_parser.set_defaults(func=cmd_decrypt)

    # train command
    train_parser = subparsers.add_parser(
        "train",
        help="Train model on encrypted data",
    )
    train_parser.add_argument(
        "-m", "--model",
        required=True,
        choices=["linear-regression", "logistic-regression", "decision-tree", "kmeans"],
        help="Model type",
    )
    train_parser.add_argument(
        "-d", "--data",
        required=True,
        help="Encrypted data file",
    )
    train_parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output model file",
    )
    train_parser.add_argument(
        "-k", "--keys",
        help="Keys directory (uses stored path if not specified)",
    )
    train_parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs",
    )
    train_parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.01,
        help="Learning rate",
    )
    train_parser.add_argument(
        "--n-clusters",
        type=int,
        default=3,
        help="Number of clusters (for K-Means)",
    )
    train_parser.add_argument(
        "--max-depth",
        type=int,
        default=4,
        help="Max tree depth (for Decision Tree)",
    )
    train_parser.add_argument(
        "--task",
        choices=["classification", "regression"],
        default="classification",
        help="Task type for Decision Tree",
    )
    train_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print training progress",
    )
    train_parser.set_defaults(func=cmd_train)

    # predict command
    predict_parser = subparsers.add_parser(
        "predict",
        help="Make predictions",
    )
    predict_parser.add_argument(
        "-m", "--model",
        required=True,
        help="Trained model file",
    )
    predict_parser.add_argument(
        "-i", "--input",
        required=True,
        help="Encrypted input data",
    )
    predict_parser.add_argument(
        "-o", "--output",
        help="Output predictions file (prints to stdout if not specified)",
    )
    predict_parser.add_argument(
        "-k", "--keys",
        help="Keys directory (uses stored path if not specified)",
    )
    predict_parser.add_argument(
        "--format",
        choices=["csv", "json", "npy"],
        default="csv",
        help="Output format",
    )
    predict_parser.add_argument(
        "--encrypted",
        action="store_true",
        help="Predict on encrypted data (FHE inference, slower)",
    )
    predict_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show progress",
    )
    predict_parser.set_defaults(func=cmd_predict)

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show info about encrypted data or model",
    )
    info_parser.add_argument(
        "path",
        help="Path to encrypted data or model file",
    )
    info_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information",
    )
    info_parser.set_defaults(func=cmd_info)

    # benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Run FHE performance benchmarks",
    )
    benchmark_parser.add_argument(
        "--poly-degree",
        type=int,
        default=8192,
        choices=[4096, 8192, 16384, 32768],
        help="Polynomial modulus degree",
    )
    benchmark_parser.add_argument(
        "--vector-size",
        type=int,
        default=100,
        help="Test vector size",
    )
    benchmark_parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations for averaging",
    )
    benchmark_parser.set_defaults(func=cmd_benchmark)

    # version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show version",
    )
    version_parser.set_defaults(func=cmd_version)

    # blockchain command group
    blockchain_parser = subparsers.add_parser(
        "blockchain",
        help="Blockchain operations for model verification",
    )
    blockchain_subparsers = blockchain_parser.add_subparsers(dest="blockchain_command", help="Blockchain commands")

    # blockchain connect
    bc_connect_parser = blockchain_subparsers.add_parser(
        "connect",
        help="Test blockchain connection",
    )
    bc_connect_parser.add_argument(
        "-n", "--network",
        default="arbitrum-sepolia",
        choices=["arbitrum", "arbitrum-sepolia", "ethereum", "ethereum-sepolia", "local"],
        help="Network to connect to",
    )
    bc_connect_parser.add_argument(
        "--rpc",
        help="Custom RPC URL",
    )
    bc_connect_parser.add_argument(
        "-k", "--private-key",
        help="Private key (for balance check)",
    )
    bc_connect_parser.set_defaults(func=cmd_blockchain_connect)

    # blockchain register
    bc_register_parser = blockchain_subparsers.add_parser(
        "register",
        help="Register a model on blockchain",
    )
    bc_register_parser.add_argument(
        "-m", "--model",
        required=True,
        help="Model file to register",
    )
    bc_register_parser.add_argument(
        "-c", "--contract",
        required=True,
        help="ModelRegistry contract address",
    )
    bc_register_parser.add_argument(
        "-k", "--private-key",
        required=True,
        help="Private key for signing transactions",
    )
    bc_register_parser.add_argument(
        "-n", "--network",
        default="arbitrum-sepolia",
        choices=["arbitrum", "arbitrum-sepolia", "local"],
        help="Network to use",
    )
    bc_register_parser.add_argument(
        "--rpc",
        help="Custom RPC URL",
    )
    bc_register_parser.add_argument(
        "-v", "--version",
        help="Model version (default: from model file)",
    )
    bc_register_parser.set_defaults(func=cmd_blockchain_register)

    # blockchain checkpoint
    bc_checkpoint_parser = blockchain_subparsers.add_parser(
        "checkpoint",
        help="Save a training checkpoint to blockchain",
    )
    bc_checkpoint_parser.add_argument(
        "-m", "--model",
        required=True,
        help="Model file with weights",
    )
    bc_checkpoint_parser.add_argument(
        "--model-id",
        required=True,
        help="On-chain model ID (from register)",
    )
    bc_checkpoint_parser.add_argument(
        "-e", "--epoch",
        type=int,
        required=True,
        help="Training epoch number",
    )
    bc_checkpoint_parser.add_argument(
        "-c", "--contract",
        required=True,
        help="ModelRegistry contract address",
    )
    bc_checkpoint_parser.add_argument(
        "-k", "--private-key",
        required=True,
        help="Private key for signing",
    )
    bc_checkpoint_parser.add_argument(
        "-n", "--network",
        default="arbitrum-sepolia",
        choices=["arbitrum", "arbitrum-sepolia", "local"],
        help="Network to use",
    )
    bc_checkpoint_parser.add_argument(
        "--rpc",
        help="Custom RPC URL",
    )
    bc_checkpoint_parser.set_defaults(func=cmd_blockchain_checkpoint)

    # blockchain verify
    bc_verify_parser = blockchain_subparsers.add_parser(
        "verify",
        help="Verify a model on blockchain",
    )
    bc_verify_parser.add_argument(
        "--model-id",
        required=True,
        help="On-chain model ID",
    )
    bc_verify_parser.add_argument(
        "-c", "--contract",
        required=True,
        help="ModelRegistry contract address",
    )
    bc_verify_parser.add_argument(
        "-n", "--network",
        default="arbitrum-sepolia",
        choices=["arbitrum", "arbitrum-sepolia", "local"],
        help="Network to use",
    )
    bc_verify_parser.add_argument(
        "--rpc",
        help="Custom RPC URL",
    )
    bc_verify_parser.add_argument(
        "-m", "--model",
        help="Local model file to verify against chain",
    )
    bc_verify_parser.add_argument(
        "-e", "--epoch",
        type=int,
        help="Epoch to verify",
    )
    bc_verify_parser.set_defaults(func=cmd_blockchain_verify)

    # api-key command group
    api_key_parser = subparsers.add_parser(
        "api-key",
        help="Manage API keys",
    )
    api_key_subparsers = api_key_parser.add_subparsers(dest="api_key_command", help="API key commands")

    # api-key create
    api_key_create_parser = api_key_subparsers.add_parser(
        "create",
        help="Create a new API key",
    )
    api_key_create_parser.add_argument(
        "-n", "--name",
        required=True,
        help="Human-readable name for the key",
    )
    api_key_create_parser.add_argument(
        "-p", "--permissions",
        default="read,write",
        help="Comma-separated permissions (read,write,admin)",
    )
    api_key_create_parser.add_argument(
        "-r", "--rate-limit",
        type=int,
        default=100,
        help="Rate limit (requests per minute)",
    )
    api_key_create_parser.set_defaults(func=cmd_api_key_create)

    # api-key list
    api_key_list_parser = api_key_subparsers.add_parser(
        "list",
        help="List all API keys",
    )
    api_key_list_parser.set_defaults(func=cmd_api_key_list)

    # api-key revoke
    api_key_revoke_parser = api_key_subparsers.add_parser(
        "revoke",
        help="Revoke an API key",
    )
    api_key_revoke_parser.add_argument(
        "key_hash",
        help="First 12 characters of the key hash",
    )
    api_key_revoke_parser.set_defaults(func=cmd_api_key_revoke)

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.version:
        return cmd_version(args)

    if not args.command:
        parser.print_help()
        return 0

    # Handle api-key without subcommand
    if args.command == "api-key" and not getattr(args, "api_key_command", None):
        print("Usage: xcapit-fhe api-key <command>")
        print("\nCommands:")
        print("  create    Create a new API key")
        print("  list      List all API keys")
        print("  revoke    Revoke an API key")
        return 0

    # Handle blockchain without subcommand
    if args.command == "blockchain" and not getattr(args, "blockchain_command", None):
        print("Usage: xcapit-fhe blockchain <command>")
        print("\nCommands:")
        print("  connect     Test blockchain connection")
        print("  register    Register a model on blockchain")
        print("  checkpoint  Save a training checkpoint")
        print("  verify      Verify a model on blockchain")
        return 0

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


__all__ = [
    "main",
    "create_parser",
    "get_version",
    # Commands
    "cmd_init",
    "cmd_encrypt",
    "cmd_decrypt",
    "cmd_train",
    "cmd_predict",
    "cmd_blockchain_connect",
    "cmd_blockchain_register",
    "cmd_blockchain_checkpoint",
    "cmd_blockchain_verify",
    "cmd_api_key_create",
    "cmd_api_key_list",
    "cmd_api_key_revoke",
    "cmd_benchmark",
    "cmd_version",
    "cmd_info",
]
