#!/usr/bin/env python3
"""Xcapit FHE-ML SDK Command Line Interface.

Provides CLI commands for:
- Encrypting/decrypting data
- Training models on encrypted data
- Making predictions
- Managing encryption keys
- Interacting with blockchain

Usage:
    xcapit-fhe encrypt --input data.csv --output encrypted.bin
    xcapit-fhe train --model linear-regression --data encrypted.bin
    xcapit-fhe predict --model model.bin --input encrypted.bin
"""

import argparse
import json
import os
import pickle
import sys
from pathlib import Path
from typing import Optional

import numpy as np


def get_version() -> str:
    """Get SDK version."""
    try:
        from . import __version__
        return __version__
    except ImportError:
        return "0.1.0"


def cmd_version(args) -> int:
    """Print version information."""
    print(f"Xcapit FHE-ML SDK v{get_version()}")
    return 0


def cmd_init(args) -> int:
    """Initialize a new FHE context and save keys."""
    from .encryption import FHEContextManager, SecurityLevel

    print("Initializing FHE context...")

    # Parse security level
    security_map = {
        "128": SecurityLevel.TC128,
        "192": SecurityLevel.TC192,
        "256": SecurityLevel.TC256,
    }
    security = security_map.get(args.security, SecurityLevel.TC128)

    # Create context
    manager = FHEContextManager()
    manager.generate_context(
        poly_modulus_degree=args.poly_degree,
        security_level=security,
    )

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save keys
    keys_path = output_dir / "keys"
    keys_path.mkdir(exist_ok=True)

    context_path = keys_path / "context.bin"
    manager.save_context(str(context_path))
    print(f"  Context saved: {context_path}")

    secret_path = keys_path / "secret.key"
    manager.save_secret_key(str(secret_path))
    print(f"  Secret key saved: {secret_path}")

    public_path = keys_path / "public.key"
    manager.save_public_key(str(public_path))
    print(f"  Public key saved: {public_path}")

    # Save config
    config = {
        "poly_modulus_degree": args.poly_degree,
        "security_level": args.security,
        "version": get_version(),
    }
    config_path = output_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\nFHE context initialized in: {output_dir}")
    print("\nIMPORTANT: Keep secret.key secure and never share it!")
    return 0


def cmd_encrypt(args) -> int:
    """Encrypt data from CSV file."""
    import pandas as pd
    from .encryption import FHEContextManager, CKKSEncryptor
    from .utils import SecureDataLoader

    print(f"Encrypting data from: {args.input}")

    # Load context
    keys_dir = Path(args.keys)
    if not keys_dir.exists():
        print(f"Error: Keys directory not found: {keys_dir}")
        return 1

    manager = FHEContextManager()
    manager.load_context(str(keys_dir / "context.bin"))
    manager.load_public_key(str(keys_dir / "public.key"))

    encryptor = CKKSEncryptor(manager)

    # Load data
    df = pd.read_csv(args.input)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    # Determine target column
    target_col = args.target
    if target_col and target_col not in df.columns:
        print(f"Error: Target column '{target_col}' not found")
        return 1

    # Encrypt
    loader = SecureDataLoader(encryptor)

    if target_col:
        X = df.drop(columns=[target_col]).values
        y = df[target_col].values
        encrypted = loader.encrypt_dataset(X, y)
    else:
        X = df.values
        encrypted = loader.encrypt_matrix(X)

    # Save
    output_path = Path(args.output)
    with open(output_path, "wb") as f:
        pickle.dump({
            "data": encrypted,
            "columns": list(df.columns),
            "target": target_col,
            "n_samples": len(df),
        }, f)

    print(f"  Encrypted data saved: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
    return 0


def cmd_train(args) -> int:
    """Train a model on encrypted data."""
    from .encryption import FHEContextManager, CKKSEncryptor
    from .models import (
        FHEModel,
        ModelConfig,
        LinearRegression,
        LogisticRegression,
        DecisionTree,
        KMeans,
    )

    print(f"Training {args.model} model...")

    # Load context
    keys_dir = Path(args.keys)
    manager = FHEContextManager()
    manager.load_context(str(keys_dir / "context.bin"))
    manager.load_secret_key(str(keys_dir / "secret.key"))

    encryptor = CKKSEncryptor(manager)

    # Load encrypted data
    with open(args.data, "rb") as f:
        data_bundle = pickle.load(f)

    encrypted_data = data_bundle["data"]

    # Create model config
    config = ModelConfig(
        learning_rate=args.learning_rate,
        n_epochs=args.epochs,
        verbose=args.verbose,
    )

    # Create model
    model_map = {
        "linear-regression": lambda: LinearRegression(config=config, encryptor=encryptor),
        "logistic-regression": lambda: LogisticRegression(config=config, encryptor=encryptor),
        "decision-tree": lambda: DecisionTree(encryptor=encryptor),
        "kmeans": lambda: KMeans(n_clusters=args.n_clusters, encryptor=encryptor),
    }

    if args.model not in model_map:
        print(f"Error: Unknown model '{args.model}'")
        print(f"Available: {list(model_map.keys())}")
        return 1

    model = model_map[args.model]()

    # Train
    print(f"  Training for {args.epochs} epochs...")
    model.fit(encrypted_data)

    print(f"  Training complete!")
    if hasattr(model, "history") and model.history.losses:
        print(f"  Final loss: {model.history.losses[-1]:.6f}")

    # Save model
    output_path = Path(args.output)
    with open(output_path, "wb") as f:
        pickle.dump({
            "model_type": args.model,
            "params": model.get_params(),
            "config": {
                "learning_rate": args.learning_rate,
                "n_epochs": args.epochs,
            },
        }, f)

    print(f"  Model saved: {output_path}")
    return 0


def cmd_predict(args) -> int:
    """Make predictions with a trained model."""
    from .encryption import FHEContextManager, CKKSEncryptor
    from .models import LinearRegression, LogisticRegression, DecisionTree, KMeans

    print("Making predictions...")

    # Load context
    keys_dir = Path(args.keys)
    manager = FHEContextManager()
    manager.load_context(str(keys_dir / "context.bin"))
    manager.load_secret_key(str(keys_dir / "secret.key"))

    encryptor = CKKSEncryptor(manager)

    # Load model
    with open(args.model, "rb") as f:
        model_bundle = pickle.load(f)

    model_type = model_bundle["model_type"]

    # Recreate model
    model_map = {
        "linear-regression": LinearRegression,
        "logistic-regression": LogisticRegression,
        "decision-tree": DecisionTree,
        "kmeans": KMeans,
    }

    model = model_map[model_type](encryptor=encryptor)
    model.set_params(model_bundle["params"])

    # Load input data
    with open(args.input, "rb") as f:
        input_bundle = pickle.load(f)

    encrypted_input = input_bundle["data"]

    # Predict
    if hasattr(encrypted_input, "X"):
        predictions = model.predict(encrypted_input.X)
    else:
        predictions = model.predict(encrypted_input)

    # Decrypt predictions
    decrypted = []
    for pred in predictions:
        decrypted.append(encryptor.decrypt_vector(pred))

    results = np.array(decrypted)

    # Save or print
    if args.output:
        np.save(args.output, results)
        print(f"  Predictions saved: {args.output}")
    else:
        print("Predictions:")
        for i, pred in enumerate(results[:10]):
            print(f"  [{i}]: {pred}")
        if len(results) > 10:
            print(f"  ... and {len(results) - 10} more")

    return 0


def cmd_info(args) -> int:
    """Show information about encrypted data or model."""
    path = Path(args.path)

    if not path.exists():
        print(f"Error: File not found: {path}")
        return 1

    with open(path, "rb") as f:
        bundle = pickle.load(f)

    print(f"File: {path}")
    print(f"Size: {path.stat().st_size / 1024:.1f} KB")
    print()

    if "model_type" in bundle:
        print("Type: Trained Model")
        print(f"  Model: {bundle['model_type']}")
        if "config" in bundle:
            print(f"  Config: {bundle['config']}")
        if "params" in bundle:
            params = bundle["params"]
            if params.get("weights") is not None:
                print(f"  Weights: {len(params['weights'])} features")
            if params.get("state"):
                print(f"  State: {params['state']}")
    elif "data" in bundle:
        print("Type: Encrypted Data")
        print(f"  Samples: {bundle.get('n_samples', 'unknown')}")
        if "columns" in bundle:
            print(f"  Columns: {bundle['columns']}")
        if "target" in bundle and bundle["target"]:
            print(f"  Target: {bundle['target']}")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="xcapit-fhe",
        description="Xcapit FHE-ML SDK - Privacy-preserving machine learning",
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
    encrypt_parser.set_defaults(func=cmd_encrypt)

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
        default="./fhe_workspace/keys",
        help="Keys directory",
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
        default="./fhe_workspace/keys",
        help="Keys directory",
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
    info_parser.set_defaults(func=cmd_info)

    # version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show version",
    )
    version_parser.set_defaults(func=cmd_version)

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

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        if os.environ.get("DEBUG"):
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
