"""Training command."""

import pickle
from pathlib import Path

from ..utils import get_version


def cmd_train(args) -> int:
    """Train a model on encrypted data."""
    from ...encryption import FHEContextManager, CKKSEncryptor
    from ...encryption.ckks_wrapper import EncryptedMatrix, EncryptedVector
    from ...models import (
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
        from ...utils.data_loader import EncryptedDataset
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


__all__ = ["cmd_train"]
