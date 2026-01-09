"""Encryption commands: init, encrypt, decrypt."""

import json
import pickle
from pathlib import Path

from ..utils import get_version


def cmd_init(args) -> int:
    """Initialize a new FHE context and save keys."""
    from ...encryption import FHEContextManager, SecurityLevel, CKKSParameters

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
    from ...utils import SecureDataLoader

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
        from ...encryption import FHEContextManager, CKKSEncryptor

        manager = FHEContextManager()
        manager.load_from_file(str(keys_dir / "context.bin"))

        # Create loader with existing context's encryptor
        from ...encryption import CKKSParameters
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
    from ...encryption import FHEContextManager, CKKSEncryptor
    from ...encryption.ckks_wrapper import EncryptedMatrix, EncryptedVector

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


__all__ = ["cmd_init", "cmd_encrypt", "cmd_decrypt"]
