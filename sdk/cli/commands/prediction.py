"""Prediction command."""

import json
import pickle
from pathlib import Path

import numpy as np


def cmd_predict(args) -> int:
    """Make predictions with a trained model."""
    import pandas as pd

    from ...encryption import CKKSEncryptor, FHEContextManager
    from ...encryption.ckks_wrapper import EncryptedMatrix
    from ...models import (
        DecisionTreeClassifier,
        DecisionTreeRegressor,
        KMeans,
        LinearRegression,
        LogisticRegression,
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
    keys_dir = (
        Path(args.keys)
        if args.keys
        else Path(model_bundle.get("keys_path", "./fhe_workspace/keys"))
    )

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
                print(f"    Processing sample {i + 1}/{n_samples}...")

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
    if (
        norm_params
        and "y_min" in norm_params
        and model_type in ["linear-regression", "decision-tree"]
    ):
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


__all__ = ["cmd_predict"]
