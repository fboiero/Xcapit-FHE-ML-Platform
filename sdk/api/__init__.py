"""REST API for Xcapit FHE-ML SDK.

Provides HTTP endpoints for:
- Model training and prediction
- Data encryption/decryption
- Key management
- Model registry
"""

from .client import APIError, ConnectionError, FHEMLClient, connect
from .server import app, create_app

__all__ = [
    # Server
    "create_app",
    "app",
    # Client
    "FHEMLClient",
    "connect",
    "APIError",
    "ConnectionError",
]
