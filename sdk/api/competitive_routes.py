"""API routes for Competitive Insights.

This module provides REST API endpoints for anonymous industry
benchmarks and competitive positioning.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .auth import get_current_company
from .consortium import ConsortiumManager

router = APIRouter(prefix="/api/competitive", tags=["competitive-insights"])


# Request/Response Models
class CompareRequest(BaseModel):
    """Request for industry comparison."""

    industry: str = Field(..., description="Industry: finance, healthcare, retail")
    metrics: Optional[dict[str, float]] = Field(None, description="Company metrics to compare")


class BenchmarkResponse(BaseModel):
    """Industry benchmark data."""

    industry: str
    benchmarks: list[dict]
    privacy_note: str


# Helper
def get_manager() -> ConsortiumManager:
    """Get consortium manager instance."""
    return ConsortiumManager()


# Endpoints
@router.get("/benchmarks/{industry}")
async def get_industry_benchmarks(
    industry: str,
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get anonymized industry benchmarks.

    Returns percentile distributions for key metrics without exposing
    individual company data.

    Industries: finance, healthcare, retail
    Metric types: accuracy, error, latency, quality, compliance
    """
    valid_industries = ["finance", "healthcare", "retail", "insurance", "manufacturing"]
    if industry not in valid_industries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Industry must be one of: {valid_industries}",
        )

    benchmarks = manager.get_industry_benchmarks(industry, metric_type)

    return {
        "industry": industry,
        "metric_type_filter": metric_type,
        "benchmark_count": len(benchmarks),
        "benchmarks": benchmarks,
        "privacy_note": "All benchmarks computed from encrypted aggregate data",
    }


@router.post("/compare")
async def compare_to_industry(
    request: CompareRequest,
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Compare your metrics against industry benchmarks.

    Provides percentile rankings showing how you perform relative
    to anonymized industry data.
    """
    try:
        result = manager.compare_to_industry(
            company_id=company["id"], industry=request.industry, metrics=request.metrics
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Comparison failed: {str(e)}"
        )


@router.get("/trends/{industry}")
async def get_industry_trends(
    industry: str,
    period: str = Query("quarterly", description="Period: monthly, quarterly, yearly"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get industry trend data.

    Shows how key metrics are changing over time across the industry.
    """
    valid_periods = ["monthly", "quarterly", "yearly"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Period must be one of: {valid_periods}",
        )

    trends = manager.get_industry_trends(industry, period)

    return {
        "industry": industry,
        "period": period,
        "trends": trends,
        "privacy_note": "Trends computed from encrypted consortium data",
    }


@router.get("/position")
async def get_competitive_position(
    consortium_id: Optional[str] = Query(None, description="Optional consortium context"),
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get your company's competitive position.

    Returns overall ranking, strengths, and improvement areas
    based on benchmark comparisons.
    """
    position = manager.get_competitive_position(
        company_id=company["id"], consortium_id=consortium_id
    )

    return position


@router.get("/stats")
async def get_competitive_stats(
    company: dict = Depends(get_current_company),
    manager: ConsortiumManager = Depends(get_manager),
):
    """Get competitive insights statistics."""
    stats = manager.get_competitive_insights_stats()
    return stats
