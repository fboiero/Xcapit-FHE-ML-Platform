"""FastAPI server for Xcapit FHE-ML SDK.

Provides REST API endpoints for privacy-preserving ML operations.

Usage:
    uvicorn sdk.api.server:app --reload
    # or
    python -m sdk.api.server
"""

import uuid
from datetime import datetime
from typing import Any, Optional

import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# SDK imports
from ..models import (
    DecisionTreeClassifier,
    DecisionTreeRegressor,
    KMeans,
    KMeansConfig,
    LinearRegression,
    LogisticRegression,
    ModelConfig,
    TreeConfig,
)
from .auth import (
    check_rate_limit,
    create_api_key,
    list_api_keys,
    optional_auth,
    rate_limiter,
    require_api_key,
    require_read,
    require_write,
    revoke_api_key,
)

# ============ Pydantic Models ============


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ModelCreateRequest(BaseModel):
    model_type: str = Field(
        ..., description="Model type: linear_regression, logistic_regression, decision_tree, kmeans"
    )
    config: Optional[dict[str, Any]] = Field(default=None, description="Model configuration")


class ModelResponse(BaseModel):
    model_id: str
    model_type: str
    status: str
    created_at: str
    config: dict[str, Any]


class TrainRequest(BaseModel):
    X: list[list[float]] = Field(..., description="Feature matrix")
    y: Optional[list[float]] = Field(None, description="Target vector (optional for clustering)")


class TrainResponse(BaseModel):
    model_id: str
    status: str
    epochs: int
    final_loss: Optional[float]
    metrics: dict[str, Any]


class PredictRequest(BaseModel):
    X: list[list[float]] = Field(..., description="Feature matrix for prediction")


class PredictResponse(BaseModel):
    model_id: str
    predictions: list[float]
    probabilities: Optional[list[list[float]]] = None


class ModelParams(BaseModel):
    weights: Optional[list[float]] = None
    bias: Optional[float] = None
    n_features: Optional[int] = None
    state: str
    extra: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ============ Database Storage ============

from .database import DatabaseManager, get_database

# In-memory cache for loaded model instances (optional, for performance)
_model_cache: dict[str, Any] = {}


def get_db() -> DatabaseManager:
    """Get database instance."""
    return get_database()


class ModelStore:
    """Database-backed model storage with optional caching."""

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self._cache: dict[str, Any] = {}

    def save(self, model_id: str, model: Any, metadata: dict) -> None:
        """Save model to database."""
        db = get_db()
        db.save_model(
            model_id=model_id,
            model_type=metadata.get("model_type", "unknown"),
            config=metadata.get("config", {}),
            status=metadata.get("status", "created"),
            params=model.get_params() if hasattr(model, "get_params") else None,
            n_features=metadata.get("n_features"),
            feature_names=metadata.get("feature_names"),
            metadata={
                "created_at": metadata.get("created_at"),
                "trained_at": metadata.get("trained_at"),
            },
        )
        if self.use_cache:
            self._cache[model_id] = model

    def get(self, model_id: str) -> tuple:
        """Get model and metadata from database."""
        db = get_db()
        record = db.get_model(model_id)

        if not record:
            raise KeyError(f"Model {model_id} not found")

        # Check cache first
        if self.use_cache and model_id in self._cache:
            model = self._cache[model_id]
        else:
            # Reconstruct model from params
            model = self._reconstruct_model(record)
            if self.use_cache:
                self._cache[model_id] = model

        metadata = {
            "model_type": record.model_type,
            "status": record.status,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "config": record.config,
            "trained_at": record.trained_at.isoformat() if record.trained_at else None,
        }

        return model, metadata

    def _reconstruct_model(self, record) -> Any:
        """Reconstruct model instance from database record."""
        model = create_model(record.model_type, record.config)

        # Load params if available
        params = get_db().get_model_params(record.id)
        if params:
            model.set_params(params)

        return model

    def delete(self, model_id: str) -> bool:
        """Delete model from database."""
        if self.use_cache and model_id in self._cache:
            del self._cache[model_id]
        return get_db().delete_model(model_id)

    def list_models(self) -> list[dict]:
        """List all models from database."""
        db = get_db()
        records = db.list_models()
        return [
            {
                "model_id": r.id,
                "model_type": r.model_type,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "config": r.config,
            }
            for r in records
        ]

    def update_after_training(
        self,
        model_id: str,
        model: Any,
        epochs: int,
        final_loss: Optional[float],
    ) -> None:
        """Update model after training completion."""
        db = get_db()
        db.update_model_status(
            model_id=model_id,
            status="trained",
            trained_at=datetime.utcnow(),
            training_epochs=epochs,
            final_loss=final_loss,
            params=model.get_params() if hasattr(model, "get_params") else None,
        )
        if self.use_cache:
            self._cache[model_id] = model


# Global store (now database-backed)
model_store = ModelStore(use_cache=True)


# ============ FastAPI App ============


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="Xcapit FHE-ML API",
        description="Privacy-preserving machine learning API using Fully Homomorphic Encryption",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include consortium routes
    from .consortium_routes import router as consortium_router

    app.include_router(consortium_router, prefix="/api/v1")

    # Include governance routes (TIER 2)
    from .governance_routes import router as governance_router

    app.include_router(governance_router, prefix="/api/v1")

    # Include compliance routes (TIER 3)
    from .compliance_routes import router as compliance_router

    app.include_router(compliance_router, prefix="/api/v1")

    # Include data quality routes (TIER 3)
    from .data_quality_routes import router as data_quality_router

    app.include_router(data_quality_router, prefix="/api/v1")

    # Include marketplace routes (TIER 3)
    from .marketplace_routes import router as marketplace_router

    app.include_router(marketplace_router, prefix="/api/v1")

    # Include sandbox routes (TIER 3)
    from .sandbox_routes import router as sandbox_router

    app.include_router(sandbox_router, prefix="/api/v1")

    # Include federated inference routes (TIER 4)
    from .federated_routes import router as federated_router

    app.include_router(federated_router, prefix="/api/v1")

    # Include explainability routes (TIER 4)
    from .explainability_routes import router as explainability_router

    app.include_router(explainability_router, prefix="/api/v1")

    # Include competitive insights routes (TIER 4)
    from .competitive_routes import router as competitive_router

    app.include_router(competitive_router, prefix="/api/v1")

    # Include ensemble routes (TIER 4)
    from .ensemble_routes import router as ensemble_router

    app.include_router(ensemble_router, prefix="/api/v1")

    return app


app = create_app()


# ============ Helper Functions ============


def create_model(model_type: str, config: Optional[dict] = None):
    """Create a model instance based on type."""
    config = config or {}

    if model_type == "linear_regression":
        model_config = ModelConfig(
            learning_rate=config.get("learning_rate", 0.01),
            n_epochs=config.get("n_epochs", 100),
            verbose=config.get("verbose", False),
        )
        return LinearRegression(config=model_config)

    elif model_type == "logistic_regression":
        model_config = ModelConfig(
            learning_rate=config.get("learning_rate", 0.01),
            n_epochs=config.get("n_epochs", 100),
            verbose=config.get("verbose", False),
        )
        return LogisticRegression(config=model_config)

    elif model_type == "decision_tree":
        tree_config = TreeConfig(
            max_depth=config.get("max_depth", 4),
            learning_rate=config.get("learning_rate", 0.1),
            n_epochs=config.get("n_epochs", 50),
        )
        task = config.get("task", "classification")
        if task == "regression":
            return DecisionTreeRegressor(config=tree_config)
        return DecisionTreeClassifier(config=tree_config)

    elif model_type == "kmeans":
        kmeans_config = KMeansConfig(
            n_clusters=config.get("n_clusters", 3),
            max_iter=config.get("max_iter", 100),
        )
        return KMeans(config=kmeans_config)

    else:
        raise ValueError(f"Unknown model type: {model_type}")


def generate_model_id() -> str:
    """Generate unique model ID."""
    return f"model_{uuid.uuid4().hex[:12]}"


# ============ API Endpoints ============


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with system metrics."""
    from ..monitoring import get_health_status

    status = get_health_status()
    return {
        "status": status.status,
        "checks": status.checks,
        "uptime_seconds": round(status.uptime_seconds, 2),
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def get_metrics_endpoint():
    """Get system metrics."""
    from ..monitoring import get_metrics

    metrics = get_metrics()
    return metrics.get_all_metrics()


# ---- Model Management ----


@app.post("/models", response_model=ModelResponse)
async def create_model_endpoint(
    request: ModelCreateRequest,
    auth: dict = Depends(require_write),
):
    """Create a new model instance (requires write permission)."""
    check_rate_limit(auth)
    try:
        model = create_model(request.model_type, request.config)
        model_id = generate_model_id()

        metadata = {
            "model_type": request.model_type,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "config": request.config or {},
        }

        model_store.save(model_id, model, metadata)

        return ModelResponse(
            model_id=model_id,
            model_type=request.model_type,
            status="created",
            created_at=metadata["created_at"],
            config=metadata["config"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/models", response_model=list[dict])
async def list_models(
    auth: dict = Depends(require_read),
):
    """List all models (requires read permission)."""
    check_rate_limit(auth)
    return model_store.list_models()


@app.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    auth: dict = Depends(require_read),
):
    """Get model details (requires read permission)."""
    check_rate_limit(auth)
    try:
        model, metadata = model_store.get(model_id)
        return ModelResponse(
            model_id=model_id,
            model_type=metadata["model_type"],
            status=metadata["status"],
            created_at=metadata["created_at"],
            config=metadata["config"],
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@app.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    auth: dict = Depends(require_write),
):
    """Delete a model (requires write permission)."""
    check_rate_limit(auth)
    if model_store.delete(model_id):
        return {"message": f"Model {model_id} deleted"}
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@app.get("/models/{model_id}/params", response_model=ModelParams)
async def get_model_params(
    model_id: str,
    auth: dict = Depends(require_read),
):
    """Get model parameters (requires read permission)."""
    check_rate_limit(auth)
    try:
        model, metadata = model_store.get(model_id)
        params = model.get_params()

        return ModelParams(
            weights=params.get("weights"),
            bias=params.get("bias"),
            n_features=params.get("n_features"),
            state=params.get("state", "unknown"),
            extra={
                k: v
                for k, v in params.items()
                if k not in ["weights", "bias", "n_features", "state"]
            },
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


# ---- Training ----


@app.post("/models/{model_id}/train", response_model=TrainResponse)
async def train_model(
    model_id: str,
    request: TrainRequest,
    auth: dict = Depends(require_write),
):
    """Train a model on provided data (requires write permission)."""
    check_rate_limit(auth)
    try:
        model, metadata = model_store.get(model_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    try:
        X = np.array(request.X)
        y = np.array(request.y) if request.y is not None else None

        # Train based on model type
        if metadata["model_type"] == "kmeans":
            model.fit(X)
        else:
            if y is None:
                raise HTTPException(
                    status_code=400, detail="Target y is required for supervised models"
                )
            model.fit(X, y)

        # Get metrics
        final_loss = None
        epochs = 0
        if hasattr(model, "history"):
            epochs = model.history.epochs
            if model.history.losses:
                final_loss = float(model.history.losses[-1])

        metrics = {}
        if hasattr(model, "inertia"):
            metrics["inertia"] = float(model.inertia)

        # Update model in database
        model_store.update_after_training(
            model_id=model_id,
            model=model,
            epochs=epochs,
            final_loss=final_loss,
        )

        return TrainResponse(
            model_id=model_id,
            status="trained",
            epochs=epochs,
            final_loss=final_loss,
            metrics=metrics,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Prediction ----


@app.post("/models/{model_id}/predict", response_model=PredictResponse)
async def predict(
    model_id: str,
    request: PredictRequest,
    auth: dict = Depends(require_read),
):
    """Make predictions with a trained model (requires read permission)."""
    check_rate_limit(auth)
    import time

    start_time = time.perf_counter()

    try:
        model, metadata = model_store.get(model_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    if metadata["status"] != "trained":
        raise HTTPException(status_code=400, detail="Model must be trained before prediction")

    try:
        X = np.array(request.X)
        predictions = model.predict_plaintext(X)

        # Get probabilities if available
        probabilities = None
        if hasattr(model, "predict_proba_plaintext"):
            try:
                proba = model.predict_proba_plaintext(X)
                probabilities = proba.tolist()
            except Exception:
                pass

        # Log prediction with auth info
        latency_ms = (time.perf_counter() - start_time) * 1000
        try:
            get_db().log_prediction(
                log_id=f"pred_{uuid.uuid4().hex[:12]}",
                model_id=model_id,
                n_samples=len(X),
                latency_ms=latency_ms,
                encrypted=False,
                api_key_name=auth.get("name") if auth else None,
            )
        except Exception:
            pass  # Don't fail prediction if logging fails

        return PredictResponse(
            model_id=model_id,
            predictions=predictions.tolist(),
            probabilities=probabilities,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Stats ----


class StatsResponse(BaseModel):
    models: dict[str, int]
    predictions: dict[str, Any]
    training_runs: dict[str, int]


@app.get("/stats", response_model=StatsResponse)
async def get_stats(
    auth: dict = Depends(require_read),
):
    """Get API usage statistics (requires read permission)."""
    check_rate_limit(auth)
    stats = get_db().get_stats()
    return StatsResponse(
        models=stats["models"],
        predictions=stats["predictions"],
        training_runs=stats["training_runs"],
    )


@app.get("/stats/predictions")
async def get_prediction_stats(
    model_id: Optional[str] = None,
    auth: dict = Depends(require_read),
):
    """Get detailed prediction statistics (requires read permission)."""
    check_rate_limit(auth)
    return get_db().get_prediction_stats(model_id=model_id)


# ---- Model Types Info ----


@app.get("/model-types")
async def get_model_types():
    """Get available model types and their configurations."""
    return {
        "model_types": [
            {
                "name": "linear_regression",
                "description": "Linear regression for continuous targets",
                "config": {
                    "learning_rate": {"type": "float", "default": 0.01},
                    "n_epochs": {"type": "int", "default": 100},
                },
            },
            {
                "name": "logistic_regression",
                "description": "Logistic regression for binary classification",
                "config": {
                    "learning_rate": {"type": "float", "default": 0.01},
                    "n_epochs": {"type": "int", "default": 100},
                },
            },
            {
                "name": "decision_tree",
                "description": "Decision tree for classification or regression",
                "config": {
                    "max_depth": {"type": "int", "default": 4},
                    "learning_rate": {"type": "float", "default": 0.1},
                    "n_epochs": {"type": "int", "default": 50},
                    "task": {
                        "type": "str",
                        "default": "classification",
                        "options": ["classification", "regression"],
                    },
                },
            },
            {
                "name": "kmeans",
                "description": "K-Means clustering",
                "config": {
                    "n_clusters": {"type": "int", "default": 3},
                    "max_iter": {"type": "int", "default": 100},
                },
            },
        ]
    }


# ---- API Key Management ----


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., description="Human-readable name for the key")
    permissions: Optional[list[str]] = Field(default=["read", "write"], description="Permissions")
    rate_limit: int = Field(default=100, description="Requests per minute")


class ApiKeyResponse(BaseModel):
    api_key: str = Field(..., description="The API key (save this, it won't be shown again)")
    key_hash: str = Field(..., description="Key hash for reference")
    name: str
    permissions: list[str]
    rate_limit: int


@app.post("/admin/api-keys", response_model=ApiKeyResponse)
async def admin_create_api_key(
    request: CreateApiKeyRequest,
    auth: dict = Depends(require_api_key(permissions=["admin"])),
):
    """Create a new API key (requires admin permission)."""
    api_key, key_hash = create_api_key(
        name=request.name,
        permissions=request.permissions,
        rate_limit=request.rate_limit,
    )
    return ApiKeyResponse(
        api_key=api_key,
        key_hash=key_hash,
        name=request.name,
        permissions=request.permissions or ["read", "write"],
        rate_limit=request.rate_limit,
    )


@app.get("/admin/api-keys")
async def admin_list_api_keys(
    auth: dict = Depends(require_api_key(permissions=["admin"])),
):
    """List all API keys (requires admin permission)."""
    return list_api_keys()


@app.delete("/admin/api-keys/{key_hash_prefix}")
async def admin_revoke_api_key(
    key_hash_prefix: str,
    auth: dict = Depends(require_api_key(permissions=["admin"])),
):
    """Revoke an API key (requires admin permission)."""
    if revoke_api_key(key_hash_prefix):
        return {"message": "API key revoked"}
    raise HTTPException(status_code=404, detail="API key not found")


@app.get("/auth/me")
async def get_current_auth(
    auth: Optional[dict] = Depends(optional_auth),
):
    """Get current authentication info."""
    if auth is None:
        return {
            "authenticated": False,
            "message": "No API key provided. Set X-API-Key header or api_key query param.",
        }
    return {
        "authenticated": True,
        "name": auth.get("name"),
        "permissions": auth.get("permissions"),
        "rate_limit": auth.get("rate_limit"),
        "remaining_requests": rate_limiter.get_remaining(auth),
    }


# ============ Main ============


def main():
    """Run the API server."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
