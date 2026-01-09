"""API routes for data quality assessment (TIER 3).

This module provides REST endpoints for:
- Data quality assessment without accessing actual content
- Quality metrics: Completeness, Consistency, Uniqueness, Validity, Freshness
- Quality rules configuration
- Quality alerts and notifications
- Quality dashboard
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .auth import get_current_company

# ============ Enums ============


class QualityMetric(str, Enum):
    """Quality metrics types."""

    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"
    FRESHNESS = "freshness"
    OVERALL = "overall"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


# ============ Request Models ============


class AssessQualityRequest(BaseModel):
    """Request to assess data quality."""

    consortium_id: str
    contribution_id: Optional[str] = None
    record_count: int = Field(..., ge=0)
    feature_count: int = Field(..., ge=0)
    null_count: int = Field(default=0, ge=0)
    duplicate_count: int = Field(default=0, ge=0)
    outlier_count: int = Field(default=0, ge=0)
    schema_violations: int = Field(default=0, ge=0, description="Records with schema issues")
    format_violations: int = Field(default=0, ge=0, description="Records with format issues")
    range_violations: int = Field(default=0, ge=0, description="Records with out-of-range values")
    last_updated: Optional[datetime] = Field(default=None, description="When data was last updated")
    metadata: Optional[dict[str, Any]] = None


class SetQualityRuleRequest(BaseModel):
    """Request to set a quality rule."""

    consortium_id: str
    metric: QualityMetric
    warning_threshold: float = Field(..., ge=0, le=100)
    critical_threshold: float = Field(..., ge=0, le=100)
    enabled: bool = True


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""

    notes: Optional[str] = Field(default=None, max_length=500)


# ============ Response Models ============


class QualityAssessmentResponse(BaseModel):
    """Data quality assessment response."""

    id: str
    consortium_id: str
    company_id: str
    company_name: Optional[str] = None
    contribution_id: Optional[str] = None
    overall_score: float
    completeness_score: float
    consistency_score: float
    uniqueness_score: float
    validity_score: float
    freshness_score: float
    record_count: int
    feature_count: int
    null_ratio: float
    duplicate_ratio: float
    outlier_ratio: float
    assessed_at: datetime
    metadata: Optional[dict[str, Any]] = None


class QualityRuleResponse(BaseModel):
    """Quality rule response."""

    id: str
    consortium_id: str
    metric: str
    warning_threshold: float
    critical_threshold: float
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class QualityAlertResponse(BaseModel):
    """Quality alert response."""

    id: str
    consortium_id: str
    company_id: str
    company_name: Optional[str] = None
    assessment_id: str
    metric: str
    current_value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus
    message: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class QualityHistoryResponse(BaseModel):
    """Quality history entry response."""

    id: str
    consortium_id: str
    company_id: str
    metric: str
    value: float
    recorded_at: datetime


class CompanyQualitySummary(BaseModel):
    """Quality summary for a company."""

    company_id: str
    company_name: Optional[str] = None
    overall_score: float
    completeness_score: float
    consistency_score: float
    uniqueness_score: float
    validity_score: float
    freshness_score: float
    total_records: int
    assessments_count: int
    last_assessment: Optional[datetime] = None


class QualityDashboardResponse(BaseModel):
    """Quality dashboard response."""

    consortium_id: str
    overall_score: float
    completeness_avg: float
    consistency_avg: float
    uniqueness_avg: float
    validity_avg: float
    freshness_avg: float
    total_records: int
    total_companies: int
    total_assessments: int
    companies: list[CompanyQualitySummary]
    active_alerts: int
    last_assessment: Optional[datetime] = None


# ============ Router ============

router = APIRouter(prefix="/quality", tags=["data-quality"])


# ============ Assessments ============


@router.post("/assess", response_model=QualityAssessmentResponse)
async def assess_data_quality(
    request: AssessQualityRequest,
    company: dict = Depends(get_current_company),
):
    """Assess data quality for a company's contribution.

    This endpoint calculates quality metrics from metadata without
    accessing the actual encrypted data content.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not an active member of this consortium"
        )

    # Assess quality using real DataQualityCalculator
    assessment = manager.assess_data_quality(
        consortium_id=request.consortium_id,
        company_id=company["id"],
        contribution_id=request.contribution_id,
        record_count=request.record_count,
        feature_count=request.feature_count,
        null_count=request.null_count,
        duplicate_count=request.duplicate_count,
        outlier_count=request.outlier_count,
        schema_violations=request.schema_violations,
        format_violations=request.format_violations,
        range_violations=request.range_violations,
        last_updated=request.last_updated,
        metadata=request.metadata,
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="data_quality_assessed",
        actor_id=company["id"],
        target_id=assessment["id"],
        target_type="quality_assessment",
        data={"overall_score": assessment["overall_score"], "record_count": request.record_count},
    )

    assessment["company_name"] = company["name"]
    return assessment


@router.get("/assessments/{consortium_id}", response_model=list[QualityAssessmentResponse])
async def get_quality_assessments(
    consortium_id: str,
    company_id: Optional[str] = None,
    limit: int = 50,
    company: dict = Depends(get_current_company),
):
    """Get quality assessments for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this consortium"
        )

    assessments = manager.get_quality_assessments(consortium_id, company_id=company_id, limit=limit)
    return assessments


@router.get("/assessments/{consortium_id}/latest", response_model=QualityAssessmentResponse)
async def get_latest_assessment(
    consortium_id: str,
    target_company_id: Optional[str] = None,
    company: dict = Depends(get_current_company),
):
    """Get the latest quality assessment for a company in a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this consortium"
        )

    # Use target company or current company
    check_company_id = target_company_id or company["id"]

    assessment = manager.get_latest_quality_assessment(consortium_id, check_company_id)

    if not assessment:
        raise HTTPException(status_code=404, detail="No assessments found for this company")

    return assessment


# ============ History ============


@router.get("/history/{consortium_id}", response_model=list[QualityHistoryResponse])
async def get_quality_history(
    consortium_id: str,
    metric: Optional[QualityMetric] = None,
    company_id: Optional[str] = None,
    days: int = 30,
    company: dict = Depends(get_current_company),
):
    """Get quality metrics history for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this consortium"
        )

    history = manager.get_quality_history(
        consortium_id, metric=metric.value if metric else None, company_id=company_id, days=days
    )
    return history


# ============ Rules ============


@router.post("/rules", response_model=QualityRuleResponse)
async def set_quality_rule(
    request: SetQualityRuleRequest,
    company: dict = Depends(get_current_company),
):
    """Set a quality rule for a consortium.

    Only consortium owners or admins can set rules.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is owner or admin
    consortium = manager.get_consortium(request.consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.role.value not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners or admins can set quality rules",
        )

    # Validate thresholds
    if request.critical_threshold > request.warning_threshold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Critical threshold must be less than or equal to warning threshold",
        )

    # Set rule
    rule = manager.set_quality_rule(
        consortium_id=request.consortium_id,
        metric=request.metric.value,
        warning_threshold=request.warning_threshold,
        critical_threshold=request.critical_threshold,
        enabled=request.enabled,
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="quality_rule_set",
        actor_id=company["id"],
        target_id=rule["id"],
        target_type="quality_rule",
        data={
            "metric": request.metric.value,
            "warning_threshold": request.warning_threshold,
            "critical_threshold": request.critical_threshold,
        },
    )

    return rule


@router.get("/rules/{consortium_id}", response_model=list[QualityRuleResponse])
async def get_quality_rules(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get quality rules for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this consortium"
        )

    rules = manager.get_quality_rules(consortium_id)
    return rules


# ============ Alerts ============


@router.get("/alerts/{consortium_id}", response_model=list[QualityAlertResponse])
async def get_quality_alerts(
    consortium_id: str,
    severity: Optional[AlertSeverity] = None,
    alert_status: Optional[AlertStatus] = None,
    company: dict = Depends(get_current_company),
):
    """Get quality alerts for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this consortium"
        )

    alerts = manager.get_quality_alerts(
        consortium_id,
        severity=severity.value if severity else None,
        status=alert_status.value if alert_status else None,
    )
    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    company: dict = Depends(get_current_company),
):
    """Acknowledge a quality alert."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Acknowledge alert
    result = manager.acknowledge_alert(
        alert_id=alert_id, acknowledged_by=company["id"], notes=request.notes
    )

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"status": "acknowledged", "alert_id": alert_id}


# ============ Dashboard ============


@router.get("/dashboard/{consortium_id}", response_model=QualityDashboardResponse)
async def get_quality_dashboard(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get data quality dashboard for a consortium.

    Returns an overview of quality metrics across all members.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this consortium"
        )

    dashboard = manager.get_consortium_quality_dashboard(consortium_id)
    return dashboard
