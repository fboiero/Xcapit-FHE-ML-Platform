"""Model serialization utilities.

Provides functions for saving and loading FHE models,
including weights, configuration, and metadata.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from ..models import BaseFHEModel


_MODEL_REGISTRY_CACHE: dict[str, type] | None = None


def _get_model_registry() -> dict[str, type]:
    """Lazily get model registry to avoid circular imports."""
    global _MODEL_REGISTRY_CACHE
    if _MODEL_REGISTRY_CACHE is not None:
        return _MODEL_REGISTRY_CACHE

    from ..models import (
        DecisionTree,
        DecisionTreeClassifier,
        DecisionTreeRegressor,
        KMeans,
        LinearRegression,
        LogisticRegression,
        MiniBatchKMeans,
    )

    _MODEL_REGISTRY_CACHE = {
        "LinearRegression": LinearRegression,
        "LogisticRegression": LogisticRegression,
        "DecisionTree": DecisionTree,
        "DecisionTreeClassifier": DecisionTreeClassifier,
        "DecisionTreeRegressor": DecisionTreeRegressor,
        "KMeans": KMeans,
        "MiniBatchKMeans": MiniBatchKMeans,
    }
    return _MODEL_REGISTRY_CACHE


def get_model_registry() -> dict[str, type]:
    """Get the model type registry.

    Returns:
        Dictionary mapping model names to model classes.
    """
    return _get_model_registry()


def compute_weights_hash(model: BaseFHEModel) -> str:
    """Compute SHA256 hash of model weights.

    Args:
        model: Trained model.

    Returns:
        Hex string hash of weights.
    """
    params = model.get_params()
    weights_data = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(weights_data.encode()).hexdigest()


def save_model(
    model: BaseFHEModel,
    path: Union[str, Path],
    include_history: bool = True,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Save a trained model to disk.

    Args:
        model: Model to save.
        path: Output file path.
        include_history: Whether to include training history.
        metadata: Additional metadata to include.

    Returns:
        Dictionary with save info (path, hash, etc).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Get model class name
    model_type = model.__class__.__name__

    # Build save data
    save_data = {
        "version": "1.0",
        "model_type": model_type,
        "params": model.get_params(),
        "saved_at": datetime.utcnow().isoformat(),
    }

    # Add config
    if hasattr(model, "_config"):
        from ..models import KMeansConfig, ModelConfig, TreeConfig

        config = model._config
        if isinstance(config, ModelConfig):
            save_data["config"] = {
                "type": "ModelConfig",
                "learning_rate": config.learning_rate,
                "n_epochs": config.n_epochs,
                "batch_size": config.batch_size,
                "verbose": config.verbose,
                "early_stopping_patience": config.early_stopping_patience,
                "tolerance": config.tolerance,
            }
        elif isinstance(config, TreeConfig):
            save_data["config"] = {
                "type": "TreeConfig",
                "max_depth": config.max_depth,
                "min_samples_split": config.min_samples_split,
                "learning_rate": config.learning_rate,
                "n_epochs": config.n_epochs,
                "temperature": config.temperature,
            }
        elif isinstance(config, KMeansConfig):
            save_data["config"] = {
                "type": "KMeansConfig",
                "n_clusters": config.n_clusters,
                "max_iter": config.max_iter,
                "tol": config.tol,
                "init_method": config.init_method.value,
            }

    # Add training history
    if include_history and hasattr(model, "history"):
        history = model.history
        save_data["history"] = {
            "losses": history.losses,
            "epochs": history.epochs,
            "metrics": history.metrics,
        }

    # Add custom metadata
    if metadata:
        save_data["metadata"] = metadata

    # Compute weights hash
    weights_hash = compute_weights_hash(model)
    save_data["weights_hash"] = weights_hash

    # Save to file
    with open(path, "wb") as f:
        pickle.dump(save_data, f)

    return {
        "path": str(path),
        "model_type": model_type,
        "weights_hash": weights_hash,
        "size_bytes": path.stat().st_size,
    }


def load_model(
    path: Union[str, Path],
    verify_hash: bool = True,
) -> BaseFHEModel:
    """Load a model from disk.

    Args:
        path: Path to saved model.
        verify_hash: Whether to verify weights hash.

    Returns:
        Loaded model instance.

    Raises:
        FileNotFoundError: If model file doesn't exist.
        ValueError: If model type is unknown or hash mismatch.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    with open(path, "rb") as f:
        save_data = pickle.load(f)

    # Get model type
    model_type = save_data.get("model_type")
    model_registry = _get_model_registry()
    if model_type not in model_registry:
        raise ValueError(f"Unknown model type: {model_type}")

    # Recreate config
    config = None
    if "config" in save_data:
        from ..models import KMeansConfig, ModelConfig, TreeConfig
        from ..models.kmeans import InitMethod

        config_data = save_data["config"]
        config_type = config_data.get("type")

        if config_type == "ModelConfig":
            config = ModelConfig(
                learning_rate=config_data.get("learning_rate", 0.01),
                n_epochs=config_data.get("n_epochs", 100),
                batch_size=config_data.get("batch_size"),
                verbose=config_data.get("verbose", False),
                early_stopping_patience=config_data.get("early_stopping_patience"),
                tolerance=config_data.get("tolerance", 1e-4),
            )
        elif config_type == "TreeConfig":
            config = TreeConfig(
                max_depth=config_data.get("max_depth", 4),
                min_samples_split=config_data.get("min_samples_split", 2),
                learning_rate=config_data.get("learning_rate", 0.1),
                n_epochs=config_data.get("n_epochs", 50),
                temperature=config_data.get("temperature", 1.0),
            )
        elif config_type == "KMeansConfig":
            config = KMeansConfig(
                n_clusters=config_data.get("n_clusters", 3),
                max_iter=config_data.get("max_iter", 100),
                tol=config_data.get("tol", 1e-4),
                init_method=InitMethod(config_data.get("init_method", "kmeans++")),
            )

    # Create model instance
    model_class = model_registry[model_type]
    if config:
        model = model_class(config=config)
    else:
        model = model_class()

    # Load params
    params = save_data.get("params", {})
    model.set_params(params)

    # Restore history
    if "history" in save_data and hasattr(model, "_history"):
        history_data = save_data["history"]
        model._history.losses = history_data.get("losses", [])
        model._history.epochs = history_data.get("epochs", 0)
        model._history.metrics = history_data.get("metrics", {})

    # Verify hash
    if verify_hash and "weights_hash" in save_data:
        current_hash = compute_weights_hash(model)
        if current_hash != save_data["weights_hash"]:
            raise ValueError("Weights hash mismatch - model may be corrupted")

    return model


def get_model_info(path: Union[str, Path]) -> dict[str, Any]:
    """Get information about a saved model without fully loading it.

    Args:
        path: Path to saved model.

    Returns:
        Dictionary with model info.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    with open(path, "rb") as f:
        save_data = pickle.load(f)

    info = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "version": save_data.get("version", "unknown"),
        "model_type": save_data.get("model_type", "unknown"),
        "saved_at": save_data.get("saved_at"),
        "weights_hash": save_data.get("weights_hash"),
    }

    # Add params summary
    params = save_data.get("params", {})
    info["n_features"] = params.get("n_features")
    info["state"] = params.get("state")

    # Add training info
    if "history" in save_data:
        history = save_data["history"]
        info["epochs_trained"] = history.get("epochs", 0)
        if history.get("losses"):
            info["final_loss"] = history["losses"][-1]

    # Add config summary
    if "config" in save_data:
        info["config_type"] = save_data["config"].get("type")

    # Add custom metadata
    if "metadata" in save_data:
        info["metadata"] = save_data["metadata"]

    return info


def export_weights_json(
    model: BaseFHEModel,
    path: Union[str, Path],
) -> None:
    """Export model weights to JSON format.

    Args:
        model: Model to export.
        path: Output JSON file path.
    """
    path = Path(path)

    params = model.get_params()

    # Convert numpy arrays to lists
    export_data = {
        "model_type": model.__class__.__name__,
        "weights": params.get("weights"),
        "bias": params.get("bias"),
        "n_features": params.get("n_features"),
        "state": params.get("state"),
        "exported_at": datetime.utcnow().isoformat(),
    }

    with open(path, "w") as f:
        json.dump(export_data, f, indent=2)


def import_weights_json(
    model: BaseFHEModel,
    path: Union[str, Path],
) -> None:
    """Import model weights from JSON format.

    Args:
        model: Model to update.
        path: Input JSON file path.
    """
    path = Path(path)

    with open(path) as f:
        import_data = json.load(f)

    params = {
        "weights": import_data.get("weights"),
        "bias": import_data.get("bias"),
        "n_features": import_data.get("n_features"),
        "state": import_data.get("state"),
    }

    model.set_params(params)
