"""FastAPI server for Xcapit FHE-ML SDK.

Provides REST API endpoints for privacy-preserving ML operations.

Usage:
    uvicorn sdk.api.server:app --reload
    # or
    python -m sdk.api.server
"""

import base64
import hashlib
import json
import pickle
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# SDK imports
from ..models import (
    LinearRegression,
    LogisticRegression,
    DecisionTreeClassifier,
    DecisionTreeRegressor,
    KMeans,
    ModelConfig,
    TreeConfig,
    KMeansConfig,
)


# ============ Pydantic Models ============

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ModelCreateRequest(BaseModel):
    model_type: str = Field(..., description="Model type: linear_regression, logistic_regression, decision_tree, kmeans")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Model configuration")


class ModelResponse(BaseModel):
    model_id: str
    model_type: str
    status: str
    created_at: str
    config: Dict[str, Any]


class TrainRequest(BaseModel):
    X: List[List[float]] = Field(..., description="Feature matrix")
    y: Optional[List[float]] = Field(None, description="Target vector (optional for clustering)")


class TrainResponse(BaseModel):
    model_id: str
    status: str
    epochs: int
    final_loss: Optional[float]
    metrics: Dict[str, Any]


class PredictRequest(BaseModel):
    X: List[List[float]] = Field(..., description="Feature matrix for prediction")


class PredictResponse(BaseModel):
    model_id: str
    predictions: List[float]
    probabilities: Optional[List[List[float]]] = None


class ModelParams(BaseModel):
    weights: Optional[List[float]] = None
    bias: Optional[float] = None
    n_features: Optional[int] = None
    state: str
    extra: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ============ Database Storage ============

from .database import get_database, DatabaseManager

# In-memory cache for loaded model instances (optional, for performance)
_model_cache: Dict[str, Any] = {}


def get_db() -> DatabaseManager:
    """Get database instance."""
    return get_database()


class ModelStore:
    """Database-backed model storage with optional caching."""

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self._cache: Dict[str, Any] = {}

    def save(self, model_id: str, model: Any, metadata: Dict) -> None:
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

    def list_models(self) -> List[Dict]:
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

    return app


app = create_app()


# ============ Helper Functions ============

def create_model(model_type: str, config: Optional[Dict] = None):
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


# ---- Model Management ----

@app.post("/models", response_model=ModelResponse)
async def create_model_endpoint(request: ModelCreateRequest):
    """Create a new model instance."""
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


@app.get("/models", response_model=List[Dict])
async def list_models():
    """List all models."""
    return model_store.list_models()


@app.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str):
    """Get model details."""
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
async def delete_model(model_id: str):
    """Delete a model."""
    if model_store.delete(model_id):
        return {"message": f"Model {model_id} deleted"}
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@app.get("/models/{model_id}/params", response_model=ModelParams)
async def get_model_params(model_id: str):
    """Get model parameters."""
    try:
        model, metadata = model_store.get(model_id)
        params = model.get_params()

        return ModelParams(
            weights=params.get("weights"),
            bias=params.get("bias"),
            n_features=params.get("n_features"),
            state=params.get("state", "unknown"),
            extra={k: v for k, v in params.items() if k not in ["weights", "bias", "n_features", "state"]},
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


# ---- Training ----

@app.post("/models/{model_id}/train", response_model=TrainResponse)
async def train_model(model_id: str, request: TrainRequest):
    """Train a model on provided data."""
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
                raise HTTPException(status_code=400, detail="Target y is required for supervised models")
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
async def predict(model_id: str, request: PredictRequest):
    """Make predictions with a trained model."""
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

        # Log prediction
        latency_ms = (time.perf_counter() - start_time) * 1000
        try:
            get_db().log_prediction(
                log_id=f"pred_{uuid.uuid4().hex[:12]}",
                model_id=model_id,
                n_samples=len(X),
                latency_ms=latency_ms,
                encrypted=False,
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
    models: Dict[str, int]
    predictions: Dict[str, Any]
    training_runs: Dict[str, int]


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get API usage statistics."""
    stats = get_db().get_stats()
    return StatsResponse(
        models=stats["models"],
        predictions=stats["predictions"],
        training_runs=stats["training_runs"],
    )


@app.get("/stats/predictions")
async def get_prediction_stats(model_id: Optional[str] = None):
    """Get detailed prediction statistics."""
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
                    "task": {"type": "str", "default": "classification", "options": ["classification", "regression"]},
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


# ============ Main ============

def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
