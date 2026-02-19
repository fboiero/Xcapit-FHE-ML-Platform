"""
Model Persistence module for FHE-ML Platform.

Provides secure save/load functionality for models with optional encryption.
Uses JSON for serialization (no pickle) for security.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type

import numpy as np

# Model registry for deserialization
_MODEL_REGISTRY: Dict[str, Type] = {}


def register_model(cls: Type) -> Type:
    """
    Decorator to register a model class for persistence.

    Args:
        cls: The model class to register

    Returns:
        The same class (allows use as decorator)
    """
    _MODEL_REGISTRY[cls.__name__] = cls
    return cls


def get_registered_model(name: str) -> Type:
    """Get a registered model class by name."""
    if name not in _MODEL_REGISTRY:
        raise ValueError(f"Unknown model type: {name}. Available: {list(_MODEL_REGISTRY.keys())}")
    return _MODEL_REGISTRY[name]


@dataclass
class ModelMetadata:
    """Metadata for a saved model."""

    model_type: str
    version: str
    created_at: str
    sdk_version: str
    checksum: str
    encrypted: bool
    compression: str
    feature_names: Optional[List[str]] = None
    n_features: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class ModelSerializer:
    """
    Serializes models to JSON format.

    Handles numpy arrays and common Python types.
    """

    @staticmethod
    def serialize(obj: Any) -> Any:
        """
        Serialize an object to JSON-compatible format.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, np.ndarray):
            return {
                "__type__": "ndarray",
                "dtype": str(obj.dtype),
                "shape": obj.shape,
                "data": base64.b64encode(obj.tobytes()).decode("ascii"),
            }
        elif isinstance(obj, (np.float32, np.float64)):
            return {"__type__": "numpy_float", "value": float(obj)}
        elif isinstance(obj, (np.int32, np.int64)):
            return {"__type__": "numpy_int", "value": int(obj)}
        elif isinstance(obj, np.bool_):
            return {"__type__": "numpy_bool", "value": bool(obj)}
        elif isinstance(obj, dict):
            return {k: ModelSerializer.serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [ModelSerializer.serialize(v) for v in obj]
        elif hasattr(obj, "__dict__"):
            # Generic object serialization
            return {
                "__type__": "object",
                "__class__": type(obj).__name__,
                "__data__": ModelSerializer.serialize(obj.__dict__),
            }
        return obj

    @staticmethod
    def deserialize(obj: Any) -> Any:
        """
        Deserialize an object from JSON format.

        Args:
            obj: JSON object to deserialize

        Returns:
            Deserialized Python object
        """
        if isinstance(obj, dict):
            if "__type__" in obj:
                type_name = obj["__type__"]
                if type_name == "ndarray":
                    data = base64.b64decode(obj["data"])
                    arr = np.frombuffer(data, dtype=obj["dtype"])
                    return arr.reshape(obj["shape"])
                elif type_name == "numpy_float":
                    return obj["value"]
                elif type_name == "numpy_int":
                    return obj["value"]
                elif type_name == "numpy_bool":
                    return obj["value"]
                elif type_name == "object":
                    # Note: For security, we don't reconstruct arbitrary objects
                    return ModelSerializer.deserialize(obj["__data__"])
            return {k: ModelSerializer.deserialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ModelSerializer.deserialize(v) for v in obj]
        return obj


class Encryptor:
    """
    Simple encryption for model files.

    Uses AES-256-GCM via XOR with key-derived stream (simplified).
    For production, use cryptography library with proper AES-GCM.
    """

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive a key from password using PBKDF2."""
        # Simplified key derivation (use hashlib.pbkdf2_hmac in production)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            iterations=100000,
            dklen=32,
        )
        return key

    @staticmethod
    def encrypt(data: bytes, password: str) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data with password.

        Args:
            data: Data to encrypt
            password: Encryption password

        Returns:
            Tuple of (encrypted_data, salt, nonce)
        """
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(12)
        key = Encryptor.derive_key(password, salt)

        # Simple XOR encryption (for demo - use AES-GCM in production)
        key_stream = bytearray()
        for i in range(0, len(data), 32):
            block_key = hashlib.sha256(key + nonce + i.to_bytes(4, "big")).digest()
            key_stream.extend(block_key)

        encrypted = bytes(a ^ b for a, b in zip(data, key_stream[: len(data)]))

        # HMAC for authentication
        mac = hmac.new(key, encrypted + nonce, hashlib.sha256).digest()

        return encrypted + mac, salt, nonce

    @staticmethod
    def decrypt(encrypted_data: bytes, password: str, salt: bytes, nonce: bytes) -> bytes:
        """
        Decrypt data with password.

        Args:
            encrypted_data: Encrypted data with MAC appended
            password: Decryption password
            salt: Salt used for key derivation
            nonce: Nonce used for encryption

        Returns:
            Decrypted data

        Raises:
            ValueError: If authentication fails
        """
        key = Encryptor.derive_key(password, salt)

        # Separate data and MAC
        mac = encrypted_data[-32:]
        ciphertext = encrypted_data[:-32]

        # Verify MAC
        expected_mac = hmac.new(key, ciphertext + nonce, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Decryption failed: invalid password or corrupted data")

        # Decrypt
        key_stream = bytearray()
        for i in range(0, len(ciphertext), 32):
            block_key = hashlib.sha256(key + nonce + i.to_bytes(4, "big")).digest()
            key_stream.extend(block_key)

        decrypted = bytes(a ^ b for a, b in zip(ciphertext, key_stream[: len(ciphertext)]))

        return decrypted


def save_model(
    model: Any,
    path: str,
    password: Optional[str] = None,
    compression: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Save a model to file.

    Args:
        model: Model to save (must have get_params or __dict__)
        path: File path to save to
        password: Optional password for encryption
        compression: Whether to compress the data
        metadata: Optional additional metadata

    Returns:
        Path to saved file

    Example:
        >>> from sdk.models import LinearRegression
        >>> model = LinearRegression()
        >>> model.fit(X, y)
        >>> save_model(model, "model.fheml")
        >>> save_model(model, "model_encrypted.fheml", password="secret")
    """
    # Get model parameters
    if hasattr(model, "get_params"):
        params = model.get_params()
    elif hasattr(model, "__dict__"):
        params = model.__dict__
    else:
        raise ValueError("Model must have get_params() method or __dict__ attribute")

    # Serialize parameters
    serialized_params = ModelSerializer.serialize(params)

    # Create model data
    model_data = {
        "model_class": type(model).__name__,
        "model_module": type(model).__module__,
        "params": serialized_params,
    }

    # Get SDK version
    try:
        from . import __version__ as sdk_version
    except ImportError:
        sdk_version = "unknown"

    # Create metadata
    model_json = json.dumps(model_data, sort_keys=True)
    checksum = hashlib.sha256(model_json.encode()).hexdigest()

    model_metadata = ModelMetadata(
        model_type=type(model).__name__,
        version="1.0",
        created_at=datetime.utcnow().isoformat(),
        sdk_version=sdk_version,
        checksum=checksum,
        encrypted=password is not None,
        compression="gzip" if compression else "none",
        n_features=getattr(model, "n_features_", None),
        feature_names=getattr(model, "feature_names_", None),
        custom_metadata=metadata,
    )

    # Prepare data
    data = model_json.encode()

    if compression:
        data = gzip.compress(data)

    # Encrypt if password provided
    salt = None
    nonce = None
    if password:
        data, salt, nonce = Encryptor.encrypt(data, password)

    # Create final file structure
    file_data = {
        "format": "fheml",
        "format_version": "1.0",
        "metadata": asdict(model_metadata),
        "data": base64.b64encode(data).decode("ascii"),
    }

    if salt:
        file_data["salt"] = base64.b64encode(salt).decode("ascii")
    if nonce:
        file_data["nonce"] = base64.b64encode(nonce).decode("ascii")

    # Write to file
    with open(path, "w") as f:
        json.dump(file_data, f, indent=2)

    return path


def load_model(
    path: str,
    password: Optional[str] = None,
    verify_checksum: bool = True,
) -> Any:
    """
    Load a model from file.

    Args:
        path: Path to model file
        password: Password if file is encrypted
        verify_checksum: Whether to verify data integrity

    Returns:
        Loaded model instance

    Example:
        >>> model = load_model("model.fheml")
        >>> model = load_model("model_encrypted.fheml", password="secret")
    """
    with open(path) as f:
        file_data = json.load(f)

    # Verify format
    if file_data.get("format") != "fheml":
        raise ValueError("Invalid file format")

    metadata = ModelMetadata(**file_data["metadata"])
    data = base64.b64decode(file_data["data"])

    # Decrypt if needed
    if metadata.encrypted:
        if not password:
            raise ValueError("Password required for encrypted model")
        salt = base64.b64decode(file_data["salt"])
        nonce = base64.b64decode(file_data["nonce"])
        data = Encryptor.decrypt(data, password, salt, nonce)

    # Decompress if needed
    if metadata.compression == "gzip":
        data = gzip.decompress(data)

    # Parse model data
    model_json = data.decode()

    # Verify checksum
    if verify_checksum:
        checksum = hashlib.sha256(model_json.encode()).hexdigest()
        if checksum != metadata.checksum:
            raise ValueError("Checksum verification failed: data may be corrupted")

    model_data = json.loads(model_json)

    # Deserialize parameters
    params = ModelSerializer.deserialize(model_data["params"])

    # Get model class
    model_class_name = model_data["model_class"]

    # Try to get from registry
    if model_class_name in _MODEL_REGISTRY:
        model_class = _MODEL_REGISTRY[model_class_name]
    else:
        # Try to import dynamically
        module_name = model_data.get("model_module", "")
        try:
            import importlib

            module = importlib.import_module(module_name)
            model_class = getattr(module, model_class_name)
        except (ImportError, AttributeError):
            raise ValueError(
                f"Unknown model class: {model_class_name}. "
                f"Register it with @register_model or ensure module is importable."
            )

    # Create model instance
    model = model_class.__new__(model_class)

    # Set parameters
    if hasattr(model, "set_params"):
        model.set_params(**params)
    else:
        for key, value in params.items():
            setattr(model, key, value)

    return model


def get_model_info(path: str) -> ModelMetadata:
    """
    Get metadata about a saved model without loading it.

    Args:
        path: Path to model file

    Returns:
        ModelMetadata object
    """
    with open(path) as f:
        file_data = json.load(f)

    return ModelMetadata(**file_data["metadata"])


def export_model_weights(model: Any) -> Dict[str, Any]:
    """
    Export model weights/parameters as a dictionary.

    Args:
        model: Model to export

    Returns:
        Dictionary of model weights
    """
    if hasattr(model, "get_params"):
        params = model.get_params()
    elif hasattr(model, "__dict__"):
        params = model.__dict__
    else:
        raise ValueError("Model must have get_params() or __dict__")

    return ModelSerializer.serialize(params)


def import_model_weights(model: Any, weights: Dict[str, Any]) -> Any:
    """
    Import weights into an existing model.

    Args:
        model: Model instance to update
        weights: Dictionary of weights

    Returns:
        Updated model
    """
    params = ModelSerializer.deserialize(weights)

    if hasattr(model, "set_params"):
        model.set_params(**params)
    else:
        for key, value in params.items():
            setattr(model, key, value)

    return model


__all__ = [
    "save_model",
    "load_model",
    "get_model_info",
    "export_model_weights",
    "import_model_weights",
    "register_model",
    "get_registered_model",
    "ModelMetadata",
    "ModelSerializer",
]
