#!/usr/bin/env python3
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
    print(f"Python: {sys.version.split()[0]}")

    # Check TenSEAL availability
    try:
        import tenseal
        print(f"TenSEAL: {tenseal.__version__}")
    except ImportError:
        print("TenSEAL: Not installed")

    return 0


def cmd_init(args) -> int:
    """Initialize a new FHE context and save keys."""
    from .encryption import FHEContextManager, SecurityLevel, CKKSParameters

    print("Initializing FHE context...")

    # Parse security level
    security_map = {
        "128": SecurityLevel.TC128,
        "192": SecurityLevel.TC192,
        "256": SecurityLevel.TC256,
    }
    security = security_map.get(args.security, SecurityLevel.TC128)

    # Create context with custom parameters
    params = CKKSParameters(
        poly_modulus_degree=args.poly_degree,
        security_level=security,
    )
    manager = FHEContextManager(params=params)
    manager.create_context()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save keys
    keys_path = output_dir / "keys"
    keys_path.mkdir(exist_ok=True)

    # Save full context (with secret key) for local use
    context_path = keys_path / "context.bin"
    manager.save_to_file(str(context_path), include_secret_key=True)
    print(f"  Full context saved: {context_path}")

    # Save public context (without secret key) for sharing with server
    public_path = keys_path / "context_public.bin"
    manager.save_to_file(str(public_path), include_secret_key=False)
    print(f"  Public context saved: {public_path}")

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
    print("\nIMPORTANT: Keep context.bin secure - it contains your secret key!")
    print("Share context_public.bin with servers for encrypted computation.")
    return 0


def cmd_encrypt(args) -> int:
    """Encrypt data from CSV file."""
    import pandas as pd
    from .utils import SecureDataLoader

    print(f"Encrypting data from: {args.input}")

    # Load CSV data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    df = pd.read_csv(input_path)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    # Validate target column
    target_col = args.target
    if target_col and target_col not in df.columns:
        print(f"Error: Target column '{target_col}' not found in data")
        print(f"Available columns: {list(df.columns)}")
        return 1

    # Check if using existing context or creating new one
    keys_dir = Path(args.keys)

    if keys_dir.exists() and (keys_dir / "context.bin").exists():
        # Load existing context
        print(f"  Loading existing FHE context from: {keys_dir}")
        from .encryption import FHEContextManager, CKKSEncryptor

        manager = FHEContextManager()
        manager.load_from_file(str(keys_dir / "context.bin"))

        # Create loader with existing context's encryptor
        from .encryption import CKKSParameters
        loader = SecureDataLoader(
            encryption_scheme="CKKS",
            params=manager._params,
            normalize=not args.no_normalize,
        )
        # Replace internal context with loaded one
        loader._context_manager = manager
        loader._encryptor = CKKSEncryptor(manager)
    else:
        # Create new context with defaults
        print("  Creating new FHE context (no existing keys found)")
        loader = SecureDataLoader(
            encryption_scheme="CKKS",
            normalize=not args.no_normalize,
        )

        # Save the new context for later use
        keys_dir.mkdir(parents=True, exist_ok=True)
        loader.context_manager.save_to_file(
            str(keys_dir / "context.bin"),
            include_secret_key=True
        )
        loader.context_manager.save_to_file(
            str(keys_dir / "context_public.bin"),
            include_secret_key=False
        )
        print(f"  New keys saved to: {keys_dir}")

    # Encrypt the data
    print("  Encrypting...")
    encrypted_dataset = loader.encrypt(df, target_column=target_col)

    print(f"  Encrypted {encrypted_dataset.n_samples} samples, {encrypted_dataset.n_features} features")
    if encrypted_dataset.y is not None:
        print(f"  Target column '{target_col}' encrypted separately")

    # Serialize encrypted data (TenSEAL objects need special handling)
    print("  Serializing...")
    serialized_X = encrypted_dataset.X.serialize()
    serialized_y = encrypted_dataset.y.serialize() if encrypted_dataset.y is not None else None

    # Save encrypted data bundle
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "serialized_X": serialized_X,
        "serialized_y": serialized_y,
        "y_shape": encrypted_dataset.y.shape if encrypted_dataset.y is not None else None,
        "columns": list(df.columns),
        "feature_names": encrypted_dataset.feature_names,
        "target": target_col,
        "n_samples": encrypted_dataset.n_samples,
        "n_features": encrypted_dataset.n_features,
        "normalization_params": encrypted_dataset.normalization_params,
        "keys_path": str(keys_dir),
        "version": get_version(),
    }

    with open(output_path, "wb") as f:
        pickle.dump(bundle, f)

    size_kb = output_path.stat().st_size / 1024
    print(f"\n  Encrypted data saved: {output_path}")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"  Expansion ratio: {size_kb / (input_path.stat().st_size / 1024):.1f}x")

    return 0


def cmd_decrypt(args) -> int:
    """Decrypt encrypted data back to CSV."""
    import pandas as pd
    from .encryption import FHEContextManager, CKKSEncryptor
    from .encryption.ckks_wrapper import EncryptedMatrix, EncryptedVector

    print(f"Decrypting data from: {args.input}")

    # Load encrypted bundle
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    with open(input_path, "rb") as f:
        bundle = pickle.load(f)

    # Load context with secret key
    keys_dir = Path(args.keys) if args.keys else Path(bundle.get("keys_path", "./fhe_workspace/keys"))

    if not (keys_dir / "context.bin").exists():
        print(f"Error: Secret key not found at {keys_dir}/context.bin")
        print("Cannot decrypt without the secret key.")
        return 1

    manager = FHEContextManager()
    manager.load_from_file(str(keys_dir / "context.bin"))
    encryptor = CKKSEncryptor(manager)

    # Deserialize encrypted data
    print("  Deserializing...")
    encrypted_X = EncryptedMatrix.deserialize(bundle["serialized_X"], manager.context)

    print("  Decrypting features...")
    X_decrypted = encryptor.decrypt_matrix(encrypted_X)

    # Denormalize if needed
    norm_params = bundle.get("normalization_params")
    if norm_params and not args.no_denormalize:
        print("  Denormalizing...")
        # Reverse [-1, 1] to [0, 1] to original
        X_decrypted = (X_decrypted + 1) / 2
        X_decrypted = X_decrypted * norm_params["range"] + norm_params["min"]

    # Create DataFrame
    feature_names = bundle.get("feature_names", [f"feature_{i}" for i in range(X_decrypted.shape[1])])
    df = pd.DataFrame(X_decrypted, columns=feature_names)

    # Decrypt target if present
    if bundle.get("serialized_y") is not None:
        print("  Decrypting target...")
        encrypted_y = EncryptedVector.deserialize(
            bundle["serialized_y"],
            manager.context,
            bundle["y_shape"]
        )
        y_decrypted = encryptor.decrypt_vector(encrypted_y)

        if norm_params and "y_min" in norm_params and not args.no_denormalize:
            y_decrypted = (y_decrypted + 1) / 2 * norm_params["y_range"] + norm_params["y_min"]

        target_name = bundle.get("target", "target")
        df[target_name] = y_decrypted[:len(df)]  # Trim to match sample count

    # Save or print
    if args.output:
        output_path = Path(args.output)
        df.to_csv(output_path, index=False)
        print(f"\n  Decrypted data saved: {output_path}")
        print(f"  Shape: {df.shape}")
    else:
        print("\nDecrypted data preview:")
        print(df.head(10).to_string())
        if len(df) > 10:
            print(f"... and {len(df) - 10} more rows")

    return 0


def cmd_train(args) -> int:
    """Train a model on encrypted data."""
    from .encryption import FHEContextManager, CKKSEncryptor
    from .encryption.ckks_wrapper import EncryptedMatrix, EncryptedVector
    from .models import (
        LinearRegression,
        LogisticRegression,
        DecisionTreeClassifier,
        DecisionTreeRegressor,
        KMeans,
        ModelConfig,
        TreeConfig,
        KMeansConfig,
    )

    print(f"Training {args.model} model...")

    # Load encrypted data
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        return 1

    with open(data_path, "rb") as f:
        bundle = pickle.load(f)

    # Load context with secret key for training
    keys_dir = Path(args.keys) if args.keys else Path(bundle.get("keys_path", "./fhe_workspace/keys"))

    if not (keys_dir / "context.bin").exists():
        print(f"Error: Keys not found at {keys_dir}")
        return 1

    manager = FHEContextManager()
    manager.load_from_file(str(keys_dir / "context.bin"))
    encryptor = CKKSEncryptor(manager)

    # Deserialize encrypted data
    print("  Deserializing encrypted data...")
    encrypted_X = EncryptedMatrix.deserialize(bundle["serialized_X"], manager.context)

    encrypted_y = None
    if bundle.get("serialized_y") is not None:
        encrypted_y = EncryptedVector.deserialize(
            bundle["serialized_y"],
            manager.context,
            bundle["y_shape"]
        )

    # For models that require plaintext training (DecisionTree, KMeans),
    # decrypt the data first
    need_plaintext = args.model in ["decision-tree", "kmeans"]

    if need_plaintext:
        print("  Decrypting data for training (model requires plaintext)...")
        X_train = encryptor.decrypt_matrix(encrypted_X)
        y_train = None
        if encrypted_y is not None:
            y_train = encryptor.decrypt_vector(encrypted_y)
            y_train = y_train[:len(X_train)]

    # Create model based on type
    model = None

    if args.model == "linear-regression":
        model = LinearRegression(
            learning_rate=args.learning_rate,
            n_epochs=args.epochs,
            verbose=args.verbose,
            encryptor=encryptor,
        )

    elif args.model == "logistic-regression":
        model = LogisticRegression(
            learning_rate=args.learning_rate,
            n_epochs=args.epochs,
            verbose=args.verbose,
            encryptor=encryptor,
        )

    elif args.model == "decision-tree":
        config = TreeConfig(
            max_depth=args.max_depth,
            learning_rate=args.learning_rate,
            n_epochs=args.epochs,
        )
        if args.task == "regression":
            model = DecisionTreeRegressor(config=config, encryptor=encryptor)
        else:
            model = DecisionTreeClassifier(config=config, encryptor=encryptor)

    elif args.model == "kmeans":
        config = KMeansConfig(
            n_clusters=args.n_clusters,
            max_iter=args.epochs,
        )
        model = KMeans(config=config, encryptor=encryptor)
    else:
        print(f"Error: Unknown model type '{args.model}'")
        return 1

    # Train
    print(f"  Training for {args.epochs} epochs...")

    if need_plaintext:
        # DecisionTree and KMeans require plaintext
        if args.model == "kmeans":
            model.fit(X_train)
        else:
            if y_train is None:
                print("Error: Target column required for supervised models")
                print("Use --target when encrypting data")
                return 1
            model.fit(X_train, y_train)
    else:
        # LinearRegression and LogisticRegression can work with encrypted data
        # They decrypt internally in a trusted environment (hybrid approach)
        from .utils.data_loader import EncryptedDataset
        encrypted_dataset = EncryptedDataset(
            X=encrypted_X,
            y=encrypted_y,
            feature_names=bundle.get("feature_names", []),
            n_samples=bundle.get("n_samples", len(encrypted_X)),
            n_features=bundle.get("n_features", encrypted_X.shape[1]),
            normalization_params=bundle.get("normalization_params"),
        )
        model.fit(encrypted_dataset)

    print("  Training complete!")

    # Show training metrics
    if hasattr(model, "history") and model.history.losses:
        print(f"  Final loss: {model.history.losses[-1]:.6f}")
    if hasattr(model, "inertia"):
        print(f"  Inertia: {model.inertia:.4f}")

    # Save model
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model_bundle = {
        "model_type": args.model,
        "params": model.get_params(),
        "config": {
            "learning_rate": args.learning_rate,
            "n_epochs": args.epochs,
            "task": args.task if args.model == "decision-tree" else None,
            "n_clusters": args.n_clusters if args.model == "kmeans" else None,
            "max_depth": args.max_depth if args.model == "decision-tree" else None,
        },
        "n_features": bundle.get("n_features"),
        "feature_names": bundle.get("feature_names"),
        "normalization_params": bundle.get("normalization_params"),
        "keys_path": str(keys_dir),
        "version": get_version(),
    }

    with open(output_path, "wb") as f:
        pickle.dump(model_bundle, f)

    print(f"\n  Model saved: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")

    return 0


def cmd_predict(args) -> int:
    """Make predictions with a trained model."""
    import pandas as pd
    from .encryption import FHEContextManager, CKKSEncryptor
    from .encryption.ckks_wrapper import EncryptedMatrix, EncryptedVector
    from .models import (
        LinearRegression,
        LogisticRegression,
        DecisionTreeClassifier,
        DecisionTreeRegressor,
        KMeans,
    )

    print("Making predictions...")

    # Load model
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: Model file not found: {model_path}")
        return 1

    with open(model_path, "rb") as f:
        model_bundle = pickle.load(f)

    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    with open(input_path, "rb") as f:
        data_bundle = pickle.load(f)

    # Load context
    keys_dir = Path(args.keys) if args.keys else Path(model_bundle.get("keys_path", "./fhe_workspace/keys"))

    if not (keys_dir / "context.bin").exists():
        print(f"Error: Keys not found at {keys_dir}")
        return 1

    manager = FHEContextManager()
    manager.load_from_file(str(keys_dir / "context.bin"))
    encryptor = CKKSEncryptor(manager)

    # Deserialize encrypted data
    print("  Deserializing encrypted data...")
    encrypted_X = EncryptedMatrix.deserialize(data_bundle["serialized_X"], manager.context)

    # Recreate model
    model_type = model_bundle["model_type"]
    model_params = model_bundle["params"]
    model_config = model_bundle.get("config", {})

    if model_type == "linear-regression":
        model = LinearRegression(encryptor=encryptor)
    elif model_type == "logistic-regression":
        model = LogisticRegression(encryptor=encryptor)
    elif model_type == "decision-tree":
        if model_config.get("task") == "regression":
            model = DecisionTreeRegressor(encryptor=encryptor)
        else:
            model = DecisionTreeClassifier(encryptor=encryptor)
    elif model_type == "kmeans":
        model = KMeans(encryptor=encryptor)
    else:
        print(f"Error: Unknown model type '{model_type}'")
        return 1

    model.set_params(model_params)

    # Determine prediction mode
    if args.encrypted:
        # Predict on encrypted data (FHE inference)
        print("  Predicting on encrypted data (FHE mode)...")

        predictions_encrypted = []
        n_samples = data_bundle.get("n_samples", len(encrypted_X))

        for i in range(n_samples):
            if args.verbose and i % 10 == 0:
                print(f"    Processing sample {i+1}/{n_samples}...")

            # Get encrypted row
            enc_row = encrypted_X.rows[i]

            # Predict
            pred_enc = model.predict(enc_row)
            predictions_encrypted.append(pred_enc)

        # Decrypt predictions
        print("  Decrypting predictions...")
        predictions = []
        for pred_enc in predictions_encrypted:
            if hasattr(pred_enc, "decrypt"):
                pred_plain = pred_enc.decrypt()
            else:
                pred_plain = encryptor.decrypt_vector(pred_enc)
            predictions.append(pred_plain[0] if len(pred_plain) == 1 else pred_plain)

        predictions = np.array(predictions)
    else:
        # Predict on plaintext (faster, for testing)
        print("  Predicting on plaintext data...")
        X_plain = encryptor.decrypt_matrix(encrypted_X)
        predictions = model.predict_plaintext(X_plain)

    # Denormalize predictions if regression
    norm_params = data_bundle.get("normalization_params")
    if norm_params and "y_min" in norm_params and model_type in ["linear-regression", "decision-tree"]:
        if model_config.get("task") != "classification":
            predictions = (predictions + 1) / 2 * norm_params["y_range"] + norm_params["y_min"]

    # Output results
    if args.output:
        output_path = Path(args.output)

        if args.format == "csv":
            df = pd.DataFrame({"prediction": predictions})
            df.to_csv(output_path, index=False)
        elif args.format == "npy":
            np.save(output_path, predictions)
        else:  # json
            with open(output_path, "w") as f:
                json.dump({"predictions": predictions.tolist()}, f, indent=2)

        print(f"\n  Predictions saved: {output_path}")
    else:
        print("\nPredictions:")
        for i, pred in enumerate(predictions[:10]):
            print(f"  [{i}]: {pred}")
        if len(predictions) > 10:
            print(f"  ... and {len(predictions) - 10} more")

    print(f"\n  Total predictions: {len(predictions)}")

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
    print(f"Version: {bundle.get('version', 'unknown')}")
    print()

    if "model_type" in bundle:
        print("Type: Trained Model")
        print(f"  Model: {bundle['model_type']}")

        config = bundle.get("config", {})
        if config:
            print("  Config:")
            for k, v in config.items():
                if v is not None:
                    print(f"    {k}: {v}")

        params = bundle.get("params", {})
        if params:
            print("  Parameters:")
            if params.get("weights") is not None:
                weights = params["weights"]
                print(f"    Weights: {len(weights)} features")
                if args.verbose:
                    print(f"    Weight values: {weights[:5]}..." if len(weights) > 5 else f"    Weight values: {weights}")
            if params.get("bias") is not None:
                print(f"    Bias: {params['bias']:.6f}")
            if params.get("state"):
                print(f"    State: {params['state']}")

        if bundle.get("feature_names"):
            print(f"  Features: {bundle['feature_names']}")

    elif "serialized_X" in bundle or "encrypted_dataset" in bundle:
        print("Type: Encrypted Dataset")
        print(f"  Samples: {bundle.get('n_samples', 'unknown')}")
        print(f"  Features: {bundle.get('n_features', 'unknown')}")

        if bundle.get("columns"):
            print(f"  Columns: {bundle['columns']}")
        if bundle.get("feature_names"):
            print(f"  Feature names: {bundle['feature_names']}")
        if bundle.get("target"):
            print(f"  Target: {bundle['target']}")
        if bundle.get("normalization_params"):
            print("  Normalized: Yes")
        if bundle.get("keys_path"):
            print(f"  Keys path: {bundle['keys_path']}")

    else:
        print("Type: Unknown")
        print(f"  Keys: {list(bundle.keys())}")

    return 0


def cmd_blockchain_connect(args) -> int:
    """Test blockchain connection."""
    from .blockchain import BlockchainConnector, Network

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
    import pickle
    from .blockchain import BlockchainConnector, Network, ModelRegistryClient

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
    import pickle
    import numpy as np
    from .blockchain import BlockchainConnector, Network, ModelRegistryClient

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
    import pickle
    import numpy as np
    from .blockchain import BlockchainConnector, Network, ModelRegistryClient

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


def cmd_api_key_create(args) -> int:
    """Create a new API key."""
    from .api.auth import create_api_key

    permissions = args.permissions.split(",") if args.permissions else ["read", "write"]

    print(f"Creating API key '{args.name}'...")
    print(f"  Permissions: {permissions}")
    print(f"  Rate limit: {args.rate_limit} req/min")

    api_key, key_hash = create_api_key(
        name=args.name,
        permissions=permissions,
        rate_limit=args.rate_limit,
    )

    print("\n" + "=" * 60)
    print("API KEY CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nAPI Key: {api_key}")
    print(f"Hash:    {key_hash[:12]}...")
    print("\nIMPORTANT: Save this API key now. It cannot be recovered!")
    print("=" * 60)

    return 0


def cmd_api_key_list(args) -> int:
    """List all API keys."""
    from .api.auth import list_api_keys

    keys = list_api_keys()

    if not keys:
        print("No API keys found.")
        print("\nCreate one with: xcapit-fhe api-key create --name 'my-key'")
        return 0

    print(f"Found {len(keys)} API key(s):\n")
    print(f"{'Name':<20} {'Hash':<15} {'Permissions':<25} {'Active':<8} {'Rate Limit'}")
    print("-" * 90)

    for key in keys:
        active = "Yes" if key["is_active"] else "No"
        print(f"{key['name']:<20} {key['key_hash']:<15} {key['permissions']:<25} {active:<8} {key['rate_limit']}")

    return 0


def cmd_api_key_revoke(args) -> int:
    """Revoke an API key."""
    from .api.auth import revoke_api_key

    print(f"Revoking API key with hash prefix: {args.key_hash}...")

    if revoke_api_key(args.key_hash):
        print("API key revoked successfully.")
        return 0
    else:
        print("Error: API key not found.")
        return 1


def cmd_benchmark(args) -> int:
    """Run FHE benchmark tests."""
    import time
    from .encryption import FHEContextManager, CKKSEncryptor, CKKSParameters

    print("Running FHE Benchmarks...")
    print("=" * 50)

    # Create context
    print("\n1. Context Creation")
    start = time.perf_counter()
    params = CKKSParameters(poly_modulus_degree=args.poly_degree)
    manager = FHEContextManager(params=params)
    manager.create_context()
    encryptor = CKKSEncryptor(manager)
    context_time = (time.perf_counter() - start) * 1000
    print(f"   Time: {context_time:.1f} ms")

    # Encryption benchmark
    print(f"\n2. Vector Encryption ({args.vector_size} elements)")
    test_vector = np.random.randn(args.vector_size).tolist()

    start = time.perf_counter()
    for _ in range(args.iterations):
        encrypted = encryptor.encrypt_vector(test_vector)
    encrypt_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {encrypt_time:.2f} ms (avg of {args.iterations})")

    # Decryption benchmark
    print("\n3. Vector Decryption")
    start = time.perf_counter()
    for _ in range(args.iterations):
        decrypted = encryptor.decrypt_vector(encrypted)
    decrypt_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {decrypt_time:.2f} ms (avg of {args.iterations})")

    # Addition benchmark
    print("\n4. Encrypted Addition")
    encrypted2 = encryptor.encrypt_vector(test_vector)
    start = time.perf_counter()
    for _ in range(args.iterations):
        result = encrypted + encrypted2
    add_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {add_time:.2f} ms (avg of {args.iterations})")

    # Multiplication benchmark
    print("\n5. Encrypted Multiplication")
    start = time.perf_counter()
    for _ in range(args.iterations):
        result = encrypted * encrypted2
    mul_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {mul_time:.2f} ms (avg of {args.iterations})")

    # Precision check
    print("\n6. Precision Check")
    original = np.array(test_vector)
    decrypted = np.array(encryptor.decrypt_vector(encrypted))
    error = np.max(np.abs(original - decrypted[:len(original)]))
    print(f"   Max error: {error:.2e}")

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Poly degree:    {args.poly_degree}")
    print(f"Vector size:    {args.vector_size}")
    print(f"Context:        {context_time:.1f} ms")
    print(f"Encrypt:        {encrypt_time:.2f} ms")
    print(f"Decrypt:        {decrypt_time:.2f} ms")
    print(f"Addition:       {add_time:.2f} ms")
    print(f"Multiplication: {mul_time:.2f} ms")
    print(f"Precision:      {error:.2e}")

    return 0


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


if __name__ == "__main__":
    sys.exit(main())
