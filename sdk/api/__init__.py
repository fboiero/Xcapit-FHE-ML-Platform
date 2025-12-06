"""REST API for Xcapit FHE-ML SDK.

Provides HTTP endpoints for:
- Model training and prediction
- Data encryption/decryption
- Key management
- Model registry
"""

from .server import create_app, app
from .client import FHEMLClient, connect, APIError, ConnectionError

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
