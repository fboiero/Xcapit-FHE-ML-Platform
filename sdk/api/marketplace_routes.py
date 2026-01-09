"""API routes for Model Marketplace (TIER 3).

This module provides REST endpoints for:
- Browsing pre-trained models by industry
- Model deployments to consortiums
- Model reviews and ratings
- Marketplace statistics
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .auth import get_current_company

# ============ Enums ============


class Industry(str, Enum):
    """Available industry categories."""

    FRAUD = "cat_fraud"
    CREDIT = "cat_credit"
    HEALTH = "cat_health"
    RETAIL = "cat_retail"
    INSURANCE = "cat_insurance"


class ModelType(str, Enum):
    """Available model types."""

    LINEAR_REGRESSION = "linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    DECISION_TREE = "decision_tree"
    KMEANS = "kmeans"


class SortBy(str, Enum):
    """Sort options for models."""

    DOWNLOADS = "downloads"
    RATING = "rating"
    NEWEST = "newest"
    ACCURACY = "accuracy"


# ============ Request Models ============


class DeployModelRequest(BaseModel):
    """Request to deploy a model to a consortium."""

    consortium_id: str
    config: Optional[dict[str, Any]] = None


class AddReviewRequest(BaseModel):
    """Request to add a model review."""

    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(default=None, max_length=100)
    comment: Optional[str] = Field(default=None, max_length=1000)
    consortium_id: Optional[str] = None


# ============ Response Models ============


class CategoryResponse(BaseModel):
    """Category response."""

    id: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    model_count: int


class ModelSummaryResponse(BaseModel):
    """Model summary response for listings."""

    id: str
    name: str
    description: Optional[str]
    industry: str
    model_type: str
    version: str
    accuracy: Optional[float]
    training_samples: Optional[int]
    pricing_type: str
    is_featured: bool
    downloads: int
    rating: float
    rating_count: int


class ModelDetailResponse(BaseModel):
    """Detailed model response."""

    id: str
    name: str
    description: Optional[str]
    industry: str
    model_type: str
    version: str
    accuracy: Optional[float]
    training_samples: Optional[int]
    features: list[str]
    use_cases: list[str]
    pricing_type: str
    price: float
    is_featured: bool
    downloads: int
    rating: float
    rating_count: int
    created_at: Optional[datetime]


class DeploymentResponse(BaseModel):
    """Deployment response."""

    id: str
    model_id: str
    model_name: Optional[str]
    consortium_id: str
    deployed_by: str
    deployed_at: Optional[datetime]
    status: str


class ReviewResponse(BaseModel):
    """Review response."""

    id: str
    model_id: str
    reviewer_id: str
    reviewer_name: Optional[str]
    rating: int
    title: Optional[str]
    comment: Optional[str]
    created_at: Optional[datetime]
    helpful_count: int


class MarketplaceStatsResponse(BaseModel):
    """Marketplace statistics response."""

    total_models: int
    total_downloads: int
    active_consortiums: int
    total_reviews: int
    average_rating: float


# ============ Router ============

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ============ Categories ============


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories():
    """Get all marketplace categories."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    categories = manager.get_marketplace_categories()
    return categories


# ============ Models ============


@router.get("/models", response_model=list[ModelSummaryResponse])
async def list_models(
    industry: Optional[Industry] = None,
    model_type: Optional[ModelType] = None,
    featured: bool = False,
    search: Optional[str] = None,
    sort_by: SortBy = SortBy.DOWNLOADS,
    limit: int = Query(default=50, le=100),
):
    """Get marketplace models with optional filters."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    models = manager.get_marketplace_models(
        industry=industry.value if industry else None,
        model_type=model_type.value if model_type else None,
        featured_only=featured,
        search=search,
        sort_by=sort_by.value,
        limit=limit,
    )
    return models


@router.get("/models/featured", response_model=list[ModelSummaryResponse])
async def get_featured_models(
    limit: int = Query(default=6, le=12),
):
    """Get featured marketplace models."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    models = manager.get_featured_models(limit=limit)
    return models


@router.get("/models/{model_id}", response_model=ModelDetailResponse)
async def get_model(model_id: str):
    """Get a specific marketplace model."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    model = manager.get_marketplace_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return model


# ============ Deployments ============


@router.post("/models/{model_id}/deploy", response_model=DeploymentResponse)
async def deploy_model(
    model_id: str,
    request: DeployModelRequest,
    company: dict = Depends(get_current_company),
):
    """Deploy a marketplace model to a consortium.

    Only consortium members with admin role can deploy models.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is admin of the consortium
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.role.value not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consortium owners or admins can deploy models",
        )

    try:
        deployment = manager.deploy_marketplace_model(
            model_id=model_id,
            consortium_id=request.consortium_id,
            deployed_by=company["id"],
            config=request.config,
        )

        # Record audit event
        manager.record_audit_event(
            consortium_id=request.consortium_id,
            event_type="model_deployed",
            actor_id=company["id"],
            target_id=model_id,
            target_type="marketplace_model",
            data={"deployment_id": deployment["id"]},
        )

        return deployment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/deployments/{consortium_id}", response_model=list[DeploymentResponse])
async def get_consortium_deployments(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get all model deployments for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this consortium"
        )

    deployments = manager.get_consortium_deployments(consortium_id)
    return deployments


@router.delete("/deployments/{deployment_id}")
async def undeploy_model(
    deployment_id: str,
    company: dict = Depends(get_current_company),
):
    """Undeploy a model from a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    success = manager.undeploy_model(deployment_id, company["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return {"status": "undeployed", "deployment_id": deployment_id}


# ============ Reviews ============


@router.post("/models/{model_id}/reviews", response_model=ReviewResponse)
async def add_review(
    model_id: str,
    request: AddReviewRequest,
    company: dict = Depends(get_current_company),
):
    """Add a review for a marketplace model."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify model exists
    model = manager.get_marketplace_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        review_id = manager.add_model_review(
            model_id=model_id,
            reviewer_id=company["id"],
            rating=request.rating,
            title=request.title,
            comment=request.comment,
            consortium_id=request.consortium_id,
        )

        return ReviewResponse(
            id=review_id,
            model_id=model_id,
            reviewer_id=company["id"],
            reviewer_name=company["name"],
            rating=request.rating,
            title=request.title,
            comment=request.comment,
            created_at=datetime.utcnow(),
            helpful_count=0,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models/{model_id}/reviews", response_model=list[ReviewResponse])
async def get_reviews(
    model_id: str,
    limit: int = Query(default=50, le=100),
):
    """Get reviews for a marketplace model."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    reviews = manager.get_model_reviews(model_id, limit=limit)
    return reviews


# ============ Statistics ============


@router.get("/stats", response_model=MarketplaceStatsResponse)
async def get_marketplace_stats():
    """Get marketplace statistics."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    stats = manager.get_marketplace_stats()
    return stats
