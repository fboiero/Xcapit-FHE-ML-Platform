"""API routes for Model Explainability.

This module provides REST API endpoints for requesting and viewing
ML model explanations without revealing training data.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from .auth import get_current_company, require_api_key
from .consortium import ConsortiumManager


router = APIRouter(prefix="/api/explainability", tags=["explainability"])


# Request/Response Models
class ExplanationRequest(BaseModel):
    """Request for model explanation."""
    consortium_id: str = Field(..., description="Consortium ID")
    explanation_type: str = Field(
        ...,
        description="Type: feature_importance, shap, decision_path, counterfactual, summary"
    )
    input_data: Optional[dict] = Field(None, description="Input data for prediction explanation")
    model_id: Optional[str] = Field(None, description="Specific model to explain")
    prediction_id: Optional[str] = Field(None, description="Specific prediction to explain")


class ExplanationResponse(BaseModel):
    """Response with explanation details."""
    request_id: str
    consortium_id: str
    explanation_type: str
    status: str
    message: str


class InsightRequest(BaseModel):
    """Request for model insights."""
    consortium_id: str = Field(..., description="Consortium ID")
    model_id: Optional[str] = Field(None, description="Specific model ID")


# Helper to get manager
def get_manager() -> ConsortiumManager:
    """Get consortium manager instance."""
    return ConsortiumManager()


# Endpoints
@router.post("/explain", response_model=ExplanationResponse)
async def request_explanation(
    request: ExplanationRequest,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Request an explanation for model predictions.

    Explanation types:
    - feature_importance: Overall feature importance ranking
    - shap: SHAP values for specific prediction
    - decision_path: How the model arrived at a decision
    - counterfactual: What changes would alter the prediction
    - summary: High-level model behavior summary
    """
    valid_types = ["feature_importance", "shap", "decision_path", "counterfactual", "summary"]
    if request.explanation_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid explanation type. Must be one of: {valid_types}"
        )

    try:
        result = manager.request_explanation(
            consortium_id=request.consortium_id,
            requester_id=company["id"],
            explanation_type=request.explanation_type,
            input_data=request.input_data,
            model_id=request.model_id,
            prediction_id=request.prediction_id,
        )

        return ExplanationResponse(
            request_id=result["request_id"],
            consortium_id=result["consortium_id"],
            explanation_type=result["explanation_type"],
            status=result["status"],
            message="Explanation request submitted successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request explanation: {str(e)}"
        )


@router.get("/explanations/{request_id}")
async def get_explanation(
    request_id: str,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get a specific explanation by request ID."""
    result = manager.get_explanation(request_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explanation not found"
        )

    # Check if requester has access
    if result.get("requester_id") != company["id"]:
        # Check if user is consortium member
        consortium = manager.get_consortium(result["consortium_id"])
        if not consortium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        members = manager.get_consortium_members(result["consortium_id"])
        member_ids = [m.get("company_id") for m in members]
        if company["id"] not in member_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a consortium member"
            )

    return result


@router.get("/explanations")
async def list_explanations(
    consortium_id: str = Query(..., description="Consortium ID"),
    explanation_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """List explanations for a consortium."""
    # Verify consortium membership
    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consortium not found"
        )

    explanations = manager.list_explanations(
        consortium_id=consortium_id,
        requester_id=company["id"],
        explanation_type=explanation_type,
        limit=limit,
    )

    return {
        "consortium_id": consortium_id,
        "count": len(explanations),
        "explanations": explanations
    }


@router.get("/feature-importance")
async def get_feature_importance(
    consortium_id: str = Query(..., description="Consortium ID"),
    model_id: Optional[str] = Query(None, description="Specific model ID"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get feature importance rankings for a consortium's model.

    Returns privacy-preserving feature importance derived from
    encrypted aggregate statistics.
    """
    # Verify consortium exists
    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consortium not found"
        )

    importance = manager.get_feature_importance(
        consortium_id=consortium_id,
        model_id=model_id,
    )

    return {
        "consortium_id": consortium_id,
        "model_id": model_id,
        "feature_count": len(importance),
        "features": importance,
        "privacy_note": "Importance scores derived from encrypted aggregate statistics"
    }


@router.post("/insights")
async def compute_model_insights(
    request: InsightRequest,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Compute and return model insights.

    Provides high-level understanding of model behavior
    without exposing individual training data.
    """
    # Verify consortium exists
    consortium = manager.get_consortium(request.consortium_id)
    if not consortium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consortium not found"
        )

    try:
        insights = manager.compute_model_insights(
            consortium_id=request.consortium_id,
            model_id=request.model_id,
        )

        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute insights: {str(e)}"
        )


@router.get("/insights/{consortium_id}")
async def get_insights(
    consortium_id: str,
    model_id: Optional[str] = Query(None, description="Specific model ID"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get existing model insights for a consortium."""
    # Verify consortium exists
    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consortium not found"
        )

    insights = manager.compute_model_insights(
        consortium_id=consortium_id,
        model_id=model_id,
    )

    return insights


@router.get("/stats")
async def get_explainability_stats(
    consortium_id: Optional[str] = Query(None, description="Filter by consortium"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get explainability statistics.

    Returns aggregate statistics about explanation requests
    and model interpretability metrics.
    """
    stats = manager.get_explainability_stats(consortium_id=consortium_id)

    return {
        "stats": stats,
        "company_id": company["id"],
        "privacy_preserved": True
    }


@router.delete("/explanations/{request_id}")
async def delete_explanation(
    request_id: str,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Delete an explanation request (only by original requester)."""
    # Get explanation to verify ownership
    explanation = manager.get_explanation(request_id)

    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explanation not found"
        )

    if explanation.get("requester_id") != company["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the original requester can delete this explanation"
        )

    # Delete from database
    try:
        with manager._get_connection() as conn:
            cursor = conn.cursor()

            # Delete results first
            cursor.execute(
                "DELETE FROM explanation_results WHERE request_id = ?",
                (request_id,)
            )

            # Delete request
            cursor.execute(
                "DELETE FROM explanation_requests WHERE id = ?",
                (request_id,)
            )

            conn.commit()

        return {
            "message": "Explanation deleted successfully",
            "request_id": request_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete explanation: {str(e)}"
        )
