"""REST API for Xcapit FHE-ML SDK.

Provides HTTP endpoints for:
- Model training and prediction
- Data encryption/decryption
- Key management
- Model registry
"""

from .server import create_app, app

__all__ = ["create_app", "app"]
