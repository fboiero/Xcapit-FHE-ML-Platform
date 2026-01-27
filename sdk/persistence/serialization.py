"""Model serialization for FHE machine learning models.

This module provides utilities for saving and loading models to/from disk.
Supports JSON and binary (pickle) formats.
"""

import json
import pickle
import gzip
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union
import numpy as np


class ModelFormat(Enum):
    """Supported model serialization formats."""

    JSON = "json"  # Human-readable, larger file size
    PICKLE = "pickle"  # Binary, faster, smaller
    COMPRESSED = "compressed"  # Gzip-compressed pickle


@dataclass
class ModelMetadata:
    """Metadata about a saved model."""

    model_type: str
    sdk_version: str
    created_at: str
    description: Optional[str] = None
    custom_metadata: Optional[dict] = None


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {"__numpy__": True, "data": obj.tolist(), "dtype": str(obj.dtype)}
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, Enum):
            return {"__enum__": True, "class": obj.__class__.__name__, "value": obj.value}
        return super().default(obj)


def numpy_decoder(obj):
    """JSON decoder hook for numpy types."""
    if "__numpy__" in obj:
        return np.array(obj["data"], dtype=obj["dtype"])
    if "__enum__" in obj:
        # Return just the value for simplicity
        return obj["value"]
    return obj


class ModelSerializer:
    """Serializer for FHE machine learning models.

    Handles serialization and deserialization of models to various formats.

    Example:
        >>> from sdk.persistence import ModelSerializer
        >>> serializer = ModelSerializer()
        >>>
        >>> # Save model
        >>> serializer.save(model, "model.json", format=ModelFormat.JSON)
        >>>
        >>> # Load model
        >>> loaded_model = serializer.load("model.json")
    """

    # Registry of model types for deserialization
    _model_registry: dict[str, type] = {}

    @classmethod
    def register_model(cls, model_type: str, model_class: type) -> None:
        """Register a model class for deserialization.

        Args:
            model_type: String identifier for the model type.
            model_class: The model class to register.
        """
        cls._model_registry[model_type] = model_class

    @classmethod
    def _get_model_class(cls, model_type: str) -> type:
        """Get model class from registry."""
        if model_type not in cls._model_registry:
            # Try to import and register on demand
            cls._auto_register_models()

        if model_type not in cls._model_registry:
            raise ValueError(f"Unknown model type: {model_type}")

        return cls._model_registry[model_type]

    @classmethod
    def _auto_register_models(cls) -> None:
        """Auto-register known model types."""
        try:
            from ..models import (
                LinearRegression,
                LogisticRegression,
                DecisionTree,
                DecisionTreeClassifier,
                DecisionTreeRegressor,
                KMeans,
                MiniBatchKMeans,
                RandomForest,
                RandomForestClassifier,
                RandomForestRegressor,
                NeuralNetwork,
                NeuralNetworkClassifier,
                NeuralNetworkRegressor,
                GradientBoosting,
                GradientBoostingClassifier,
                GradientBoostingRegressor,
            )

            models = [
                ("LinearRegression", LinearRegression),
                ("LogisticRegression", LogisticRegression),
                ("DecisionTree", DecisionTree),
                ("DecisionTreeClassifier", DecisionTreeClassifier),
                ("DecisionTreeRegressor", DecisionTreeRegressor),
                ("KMeans", KMeans),
                ("MiniBatchKMeans", MiniBatchKMeans),
                ("RandomForest", RandomForest),
                ("RandomForestClassifier", RandomForestClassifier),
                ("RandomForestRegressor", RandomForestRegressor),
                ("NeuralNetwork", NeuralNetwork),
                ("NeuralNetworkClassifier", NeuralNetworkClassifier),
                ("NeuralNetworkRegressor", NeuralNetworkRegressor),
                ("GradientBoosting", GradientBoosting),
                ("GradientBoostingClassifier", GradientBoostingClassifier),
                ("GradientBoostingRegressor", GradientBoostingRegressor),
            ]

            for name, model_class in models:
                if name not in cls._model_registry:
                    cls._model_registry[name] = model_class

        except ImportError:
            pass

    def save(
        self,
        model,
        path: Union[str, Path],
        format: ModelFormat = ModelFormat.JSON,
        description: Optional[str] = None,
        custom_metadata: Optional[dict] = None,
    ) -> None:
        """Save a model to disk.

        Args:
            model: Model to save.
            path: File path to save to.
            format: Serialization format.
            description: Optional description of the model.
            custom_metadata: Additional metadata to include.
        """
        path = Path(path)

        # Get model parameters
        params = model.get_params()
        model_type = model.__class__.__name__

        # Create metadata
        from datetime import datetime
        metadata = {
            "model_type": model_type,
            "sdk_version": self._get_sdk_version(),
            "created_at": datetime.now().isoformat(),
            "description": description,
            "custom_metadata": custom_metadata,
        }

        # Bundle everything
        data = {
            "metadata": metadata,
            "params": params,
        }

        # Save based on format
        if format == ModelFormat.JSON:
            with open(path, "w") as f:
                json.dump(data, f, cls=NumpyEncoder, indent=2)

        elif format == ModelFormat.PICKLE:
            with open(path, "wb") as f:
                pickle.dump(data, f)

        elif format == ModelFormat.COMPRESSED:
            with gzip.open(path, "wb") as f:
                pickle.dump(data, f)

    def load(
        self,
        path: Union[str, Path],
        format: Optional[ModelFormat] = None,
    ) -> Any:
        """Load a model from disk.

        Args:
            path: File path to load from.
            format: Serialization format (auto-detected if None).

        Returns:
            Loaded model instance.
        """
        path = Path(path)

        # Auto-detect format
        if format is None:
            if path.suffix == ".json":
                format = ModelFormat.JSON
            elif path.suffix == ".gz":
                format = ModelFormat.COMPRESSED
            else:
                format = ModelFormat.PICKLE

        # Load data
        if format == ModelFormat.JSON:
            with open(path, "r") as f:
                data = json.load(f, object_hook=numpy_decoder)

        elif format == ModelFormat.PICKLE:
            with open(path, "rb") as f:
                data = pickle.load(f)

        elif format == ModelFormat.COMPRESSED:
            with gzip.open(path, "rb") as f:
                data = pickle.load(f)

        # Reconstruct model
        metadata = data["metadata"]
        params = data["params"]
        model_type = metadata["model_type"]

        model_class = self._get_model_class(model_type)
        model = self._reconstruct_model(model_class, params)

        return model

    def _reconstruct_model(self, model_class: type, params: dict) -> Any:
        """Reconstruct a model from parameters.

        Args:
            model_class: The model class.
            params: Saved parameters.

        Returns:
            Reconstructed model instance.
        """
        # Create instance
        model = model_class()

        # Restore parameters
        model.set_params(params)

        return model

    def _get_sdk_version(self) -> str:
        """Get SDK version string."""
        try:
            from .. import __version__
            return __version__
        except ImportError:
            return "unknown"

    def get_metadata(
        self,
        path: Union[str, Path],
        format: Optional[ModelFormat] = None,
    ) -> ModelMetadata:
        """Get metadata from a saved model without fully loading it.

        Args:
            path: File path.
            format: Serialization format.

        Returns:
            Model metadata.
        """
        path = Path(path)

        if format is None:
            if path.suffix == ".json":
                format = ModelFormat.JSON
            elif path.suffix == ".gz":
                format = ModelFormat.COMPRESSED
            else:
                format = ModelFormat.PICKLE

        if format == ModelFormat.JSON:
            with open(path, "r") as f:
                data = json.load(f)
        elif format == ModelFormat.PICKLE:
            with open(path, "rb") as f:
                data = pickle.load(f)
        elif format == ModelFormat.COMPRESSED:
            with gzip.open(path, "rb") as f:
                data = pickle.load(f)

        metadata = data["metadata"]
        return ModelMetadata(
            model_type=metadata["model_type"],
            sdk_version=metadata["sdk_version"],
            created_at=metadata["created_at"],
            description=metadata.get("description"),
            custom_metadata=metadata.get("custom_metadata"),
        )


# Default serializer instance
_default_serializer = ModelSerializer()


def save_model(
    model,
    path: Union[str, Path],
    format: ModelFormat = ModelFormat.JSON,
    **kwargs,
) -> None:
    """Save a model to disk.

    Convenience function using default serializer.

    Args:
        model: Model to save.
        path: File path to save to.
        format: Serialization format.
        **kwargs: Additional arguments for ModelSerializer.save().

    Example:
        >>> from sdk.persistence import save_model, load_model
        >>> save_model(trained_model, "my_model.json")
        >>> loaded = load_model("my_model.json")
    """
    _default_serializer.save(model, path, format, **kwargs)


def load_model(
    path: Union[str, Path],
    format: Optional[ModelFormat] = None,
) -> Any:
    """Load a model from disk.

    Convenience function using default serializer.

    Args:
        path: File path to load from.
        format: Serialization format (auto-detected if None).

    Returns:
        Loaded model instance.

    Example:
        >>> from sdk.persistence import load_model
        >>> model = load_model("my_model.json")
        >>> predictions = model.predict(X_test)
    """
    return _default_serializer.load(path, format)
