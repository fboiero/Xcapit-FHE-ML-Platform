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


# ============ In-Memory Storage ============

class ModelStore:
    """Simple in-memory model storage."""

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict] = {}

    def save(self, model_id: str, model: Any, metadata: Dict) -> None:
        self.models[model_id] = model
        self.metadata[model_id] = metadata

    def get(self, model_id: str) -> tuple:
        if model_id not in self.models:
            raise KeyError(f"Model {model_id} not found")
        return self.models[model_id], self.metadata[model_id]

    def delete(self, model_id: str) -> bool:
        if model_id in self.models:
            del self.models[model_id]
            del self.metadata[model_id]
            return True
        return False

    def list_models(self) -> List[Dict]:
        return [
            {"model_id": mid, **meta}
            for mid, meta in self.metadata.items()
        ]


# Global store
model_store = ModelStore()


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
            model._fit_plaintext(X)
        else:
            if y is None:
                raise HTTPException(status_code=400, detail="Target y is required for supervised models")
            model._fit_plaintext(X, y)

        # Update metadata
        metadata["status"] = "trained"
        metadata["trained_at"] = datetime.utcnow().isoformat()

        # Get metrics
        final_loss = None
        if hasattr(model, "history") and model.history.losses:
            final_loss = float(model.history.losses[-1])

        metrics = {}
        if hasattr(model, "inertia"):
            metrics["inertia"] = float(model.inertia)

        return TrainResponse(
            model_id=model_id,
            status="trained",
            epochs=model.history.epochs if hasattr(model, "history") else 0,
            final_loss=final_loss,
            metrics=metrics,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Prediction ----

@app.post("/models/{model_id}/predict", response_model=PredictResponse)
async def predict(model_id: str, request: PredictRequest):
    """Make predictions with a trained model."""
    try:
        model, metadata = model_store.get(model_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    if metadata["status"] != "trained":
        raise HTTPException(status_code=400, detail="Model must be trained before prediction")

    try:
        X = np.array(request.X)
        predictions = model._predict_plaintext(X)

        # Get probabilities if available
        probabilities = None
        if hasattr(model, "_predict_proba_plaintext"):
            try:
                proba = model._predict_proba_plaintext(X)
                probabilities = proba.tolist()
            except Exception:
                pass

        return PredictResponse(
            model_id=model_id,
            predictions=predictions.tolist(),
            probabilities=probabilities,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
