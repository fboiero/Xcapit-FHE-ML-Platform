"""API routes for Multi-Model Ensemble.

This module provides REST API endpoints for creating and using
ensembles that combine models from multiple consortiums.
"""

from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from .auth import get_current_company
from .consortium import ConsortiumManager


router = APIRouter(prefix="/api/ensemble", tags=["multi-model-ensemble"])


# Request/Response Models
class CreateEnsembleRequest(BaseModel):
    """Request to create an ensemble."""
    name: str = Field(..., description="Ensemble name")
    description: str = Field(..., description="Description")
    ensemble_type: str = Field("voting", description="Type: voting, averaging, weighted, stacking, boosting")


class AddModelRequest(BaseModel):
    """Request to add a model to ensemble."""
    model_id: str = Field(..., description="Model ID to add")
    consortium_id: str = Field(..., description="Source consortium")
    model_type: str = Field(..., description="Model type")
    weight: float = Field(1.0, description="Contribution weight")


class PredictRequest(BaseModel):
    """Request for ensemble prediction."""
    input_data: Dict = Field(..., description="Input features for prediction")


# Helper
def get_manager() -> ConsortiumManager:
    """Get consortium manager instance."""
    return ConsortiumManager()


# Endpoints
@router.post("/create")
async def create_ensemble(
    request: CreateEnsembleRequest,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Create a new multi-model ensemble.

    Ensembles combine predictions from multiple models trained
    in different consortiums, enabling cross-consortium insights
    while preserving privacy.

    Types:
    - voting: Majority vote for classification
    - averaging: Simple average of predictions
    - weighted: Weighted average based on model weights
    - stacking: Meta-learner combines model outputs
    - boosting: Sequential model combination
    """
    valid_types = ["voting", "averaging", "weighted", "stacking", "boosting"]
    if request.ensemble_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ensemble type must be one of: {valid_types}"
        )

    try:
        result = manager.create_ensemble(
            name=request.name,
            description=request.description,
            owner_id=company["id"],
            ensemble_type=request.ensemble_type
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{ensemble_id}/models")
async def add_model_to_ensemble(
    ensemble_id: str,
    request: AddModelRequest,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Add a model from a consortium to the ensemble.

    Models from different consortiums can be combined to create
    more powerful predictions while each model's training data
    remains encrypted and private.
    """
    try:
        result = manager.add_model_to_ensemble(
            ensemble_id=ensemble_id,
            model_id=request.model_id,
            consortium_id=request.consortium_id,
            model_type=request.model_type,
            weight=request.weight
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{ensemble_id}")
async def get_ensemble(
    ensemble_id: str,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get ensemble details including member models."""
    result = manager.get_ensemble(ensemble_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ensemble not found"
        )

    return result


@router.get("")
async def list_ensembles(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """List available ensembles."""
    ensembles = manager.list_ensembles(
        owner_id=company["id"],
        status=status_filter,
        limit=limit
    )

    return {
        "count": len(ensembles),
        "ensembles": ensembles
    }


@router.post("/{ensemble_id}/activate")
async def activate_ensemble(
    ensemble_id: str,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Activate an ensemble for predictions.

    Requires at least 2 models in the ensemble.
    """
    try:
        result = manager.activate_ensemble(
            ensemble_id=ensemble_id,
            requester_id=company["id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{ensemble_id}/predict")
async def predict_with_ensemble(
    ensemble_id: str,
    request: PredictRequest,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Make a prediction using the ensemble.

    Combines predictions from all models in the ensemble using
    the specified combination method.

    Each model's prediction is made on encrypted data, and only
    the final combined result is returned.
    """
    try:
        result = manager.predict_with_ensemble(
            ensemble_id=ensemble_id,
            requester_id=company["id"],
            input_data=request.input_data
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{ensemble_id}/performance")
async def get_ensemble_performance(
    ensemble_id: str,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get ensemble performance metrics."""
    result = manager.get_ensemble_performance(ensemble_id)
    return result


@router.get("/stats/overview")
async def get_ensemble_stats(
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get overall ensemble statistics."""
    stats = manager.get_ensemble_stats()
    return stats


@router.delete("/{ensemble_id}/models/{model_entry_id}")
async def remove_model_from_ensemble(
    ensemble_id: str,
    model_entry_id: str,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Remove a model from an ensemble."""
    try:
        with manager._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership
            cursor.execute(
                "SELECT owner_id FROM model_ensembles WHERE id = ?",
                (ensemble_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ensemble not found"
                )

            if row["owner_id"] != company["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only ensemble owner can remove models"
                )

            cursor.execute(
                "DELETE FROM ensemble_models WHERE id = ? AND ensemble_id = ?",
                (model_entry_id, ensemble_id)
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model entry not found"
                )

            conn.commit()

        return {"message": "Model removed from ensemble", "entry_id": model_entry_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
