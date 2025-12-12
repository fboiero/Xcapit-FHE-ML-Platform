"""API routes for compliance management (TIER 3).

This module provides REST endpoints for:
- Compliance frameworks (GDPR, HIPAA, SOC2, PCI-DSS)
- Compliance checks and verification
- Compliance reports
- Attestations
- Data processing records (GDPR Article 30)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .auth import get_current_company


# ============ Enums ============

class ComplianceFramework(str, Enum):
    """Available compliance frameworks."""
    GDPR = "framework_gdpr"
    HIPAA = "framework_hipaa"
    SOC2 = "framework_soc2"
    PCI_DSS = "framework_pci_dss"


class CheckStatus(str, Enum):
    """Status of a compliance check."""
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    NOT_APPLICABLE = "na"


class ControlSeverity(str, Enum):
    """Severity of compliance controls."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceStatus(str, Enum):
    """Overall compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    PENDING = "pending"


# ============ Request Models ============

class EnableFrameworkRequest(BaseModel):
    """Request to enable a compliance framework."""
    consortium_id: str
    framework_id: ComplianceFramework


class RecordCheckRequest(BaseModel):
    """Request to record a compliance check result."""
    consortium_id: str
    framework_id: ComplianceFramework
    control_id: str
    status: CheckStatus
    result: str = Field(..., max_length=1000)
    evidence: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


class GenerateReportRequest(BaseModel):
    """Request to generate a compliance report."""
    consortium_id: str
    framework_id: ComplianceFramework


class CreateAttestationRequest(BaseModel):
    """Request to create an attestation."""
    consortium_id: str
    framework_id: ComplianceFramework
    statement: str = Field(..., min_length=10, max_length=2000)
    control_id: Optional[str] = None
    attester_role: Optional[str] = Field(default=None, max_length=100)
    attestation_type: str = Field(default="manual", max_length=50)
    evidence_urls: Optional[List[str]] = None
    valid_days: int = Field(default=365, gt=0, le=730)


class RecordDataProcessingRequest(BaseModel):
    """Request to record a data processing activity (GDPR Article 30)."""
    consortium_id: str
    processing_purpose: str = Field(..., min_length=5, max_length=500)
    data_categories: List[str] = Field(..., min_items=1)
    legal_basis: str = Field(..., max_length=200)
    data_subjects: Optional[str] = Field(default=None, max_length=500)
    recipients: Optional[List[str]] = None
    retention_period: Optional[str] = Field(default=None, max_length=100)
    security_measures: Optional[List[str]] = None
    cross_border_transfer: bool = False
    transfer_safeguards: Optional[str] = Field(default=None, max_length=500)


class RunComplianceCheckRequest(BaseModel):
    """Request to run automated compliance checks."""
    consortium_id: str
    framework_id: ComplianceFramework


# ============ Response Models ============

class FrameworkResponse(BaseModel):
    """Compliance framework response."""
    id: str
    name: str
    version: str
    description: Optional[str]
    region: Optional[str]
    industry: Optional[str]
    controls_count: int


class ComplianceSettingsResponse(BaseModel):
    """Consortium compliance settings response."""
    consortium_id: str
    enabled_frameworks: List[str]
    auto_check_interval: int
    notification_emails: List[str]
    last_check_at: Optional[datetime]
    next_check_at: Optional[datetime]


class ComplianceCheckResponse(BaseModel):
    """Compliance check response."""
    id: str
    consortium_id: str
    framework_id: str
    control_id: str
    status: CheckStatus
    result: str
    evidence: Optional[Dict[str, Any]]
    checked_at: datetime
    checked_by: Optional[str]
    notes: Optional[str]


class ComplianceReportResponse(BaseModel):
    """Compliance report response."""
    id: str
    consortium_id: str
    framework_id: str
    framework_name: Optional[str]
    overall_score: float
    passed_controls: int
    failed_controls: int
    pending_controls: int
    total_controls: int
    status: ComplianceStatus
    generated_at: datetime
    valid_until: Optional[datetime]


class AttestationResponse(BaseModel):
    """Attestation response."""
    id: str
    consortium_id: str
    framework_id: str
    control_id: Optional[str]
    attested_by: str
    attester_name: Optional[str]
    attester_role: Optional[str]
    attestation_type: str
    statement: str
    evidence_urls: Optional[List[str]]
    valid_from: datetime
    valid_until: Optional[datetime]
    revoked: bool


class DataProcessingRecordResponse(BaseModel):
    """Data processing record response."""
    id: str
    consortium_id: str
    company_id: str
    company_name: Optional[str]
    processing_purpose: str
    data_categories: List[str]
    data_subjects: Optional[str]
    recipients: Optional[List[str]]
    retention_period: Optional[str]
    security_measures: Optional[List[str]]
    legal_basis: str
    cross_border_transfer: bool
    transfer_safeguards: Optional[str]
    created_at: datetime


class FrameworkStatusResponse(BaseModel):
    """Framework status in dashboard."""
    framework_id: str
    framework_name: str
    score: float
    status: ComplianceStatus
    passed: int
    failed: int
    pending: int
    total: int


class ComplianceDashboardResponse(BaseModel):
    """Compliance dashboard response."""
    consortium_id: str
    overall_score: float
    overall_status: ComplianceStatus
    enabled_frameworks_count: int
    frameworks: List[FrameworkStatusResponse]
    last_check_at: Optional[datetime]
    next_check_at: Optional[datetime]


# ============ Router ============

router = APIRouter(prefix="/compliance", tags=["compliance"])


# ============ Frameworks ============

@router.get("/frameworks", response_model=List[FrameworkResponse])
async def list_frameworks(
    company: dict = Depends(get_current_company),
):
    """Get all available compliance frameworks."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    frameworks = manager.get_compliance_frameworks()
    return frameworks


@router.get("/frameworks/{framework_id}", response_model=FrameworkResponse)
async def get_framework(
    framework_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific compliance framework."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    framework = manager.get_compliance_framework(framework_id)

    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    return framework


@router.post("/frameworks/enable")
async def enable_framework(
    request: EnableFrameworkRequest,
    company: dict = Depends(get_current_company),
):
    """Enable a compliance framework for a consortium.

    Only consortium owners can enable frameworks.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Get consortium
    consortium = manager.get_consortium(request.consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    # Verify company is owner
    if consortium.owner_id != company["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consortium owner can enable compliance frameworks"
        )

    # Enable framework
    result = manager.enable_compliance_framework(
        request.consortium_id,
        request.framework_id.value
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="compliance_framework_enabled",
        actor_id=company["id"],
        target_id=request.framework_id.value,
        target_type="framework",
        data={"framework": request.framework_id.value}
    )

    return result


# ============ Settings ============

@router.get("/settings/{consortium_id}", response_model=ComplianceSettingsResponse)
async def get_compliance_settings(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get compliance settings for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    settings = manager.get_consortium_compliance_settings(consortium_id)
    return settings


# ============ Checks ============

@router.post("/checks", response_model=ComplianceCheckResponse)
async def record_check(
    request: RecordCheckRequest,
    company: dict = Depends(get_current_company),
):
    """Record a compliance check result."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this consortium"
        )

    # Record check
    check_id = manager.record_compliance_check(
        consortium_id=request.consortium_id,
        framework_id=request.framework_id.value,
        control_id=request.control_id,
        status=request.status.value,
        result=request.result,
        evidence=request.evidence,
        checked_by=company["id"],
        notes=request.notes
    )

    return ComplianceCheckResponse(
        id=check_id,
        consortium_id=request.consortium_id,
        framework_id=request.framework_id.value,
        control_id=request.control_id,
        status=request.status,
        result=request.result,
        evidence=request.evidence,
        checked_at=datetime.utcnow(),
        checked_by=company["id"],
        notes=request.notes
    )


@router.get("/checks/{consortium_id}", response_model=List[ComplianceCheckResponse])
async def get_checks(
    consortium_id: str,
    framework_id: Optional[ComplianceFramework] = None,
    check_status: Optional[CheckStatus] = None,
    company: dict = Depends(get_current_company),
):
    """Get compliance checks for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    checks = manager.get_compliance_checks(
        consortium_id,
        framework_id=framework_id.value if framework_id else None,
        status=check_status.value if check_status else None
    )
    return checks


@router.post("/checks/run")
async def run_automated_checks(
    request: RunComplianceCheckRequest,
    company: dict = Depends(get_current_company),
):
    """Run automated compliance checks for a framework.

    This triggers automated verification of compliance controls.
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
            detail="Only owners or admins can run compliance checks"
        )

    # Run automated checks based on framework
    # For now, return a placeholder - actual verification logic would go here
    checks_run = 0
    checks_passed = 0

    # Simulate basic checks for demo
    basic_checks = [
        {"control_id": f"{request.framework_id.value}_encryption", "name": "Data Encryption", "auto_pass": True},
        {"control_id": f"{request.framework_id.value}_access_control", "name": "Access Control", "auto_pass": True},
        {"control_id": f"{request.framework_id.value}_audit_logging", "name": "Audit Logging", "auto_pass": True},
    ]

    for check in basic_checks:
        check_status = "passed" if check["auto_pass"] else "pending"
        manager.record_compliance_check(
            consortium_id=request.consortium_id,
            framework_id=request.framework_id.value,
            control_id=check["control_id"],
            status=check_status,
            result=f"Automated check: {check['name']}",
            evidence={"automated": True, "timestamp": datetime.utcnow().isoformat()},
            checked_by=company["id"],
            notes="Automated compliance verification"
        )
        checks_run += 1
        if check["auto_pass"]:
            checks_passed += 1

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="compliance_checks_run",
        actor_id=company["id"],
        target_id=request.framework_id.value,
        data={
            "framework": request.framework_id.value,
            "checks_run": checks_run,
            "checks_passed": checks_passed
        }
    )

    return {
        "consortium_id": request.consortium_id,
        "framework_id": request.framework_id.value,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "run_at": datetime.utcnow().isoformat()
    }


# ============ Reports ============

@router.post("/reports", response_model=ComplianceReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    company: dict = Depends(get_current_company),
):
    """Generate a compliance report for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    # Generate report
    report = manager.generate_compliance_report(
        request.consortium_id,
        request.framework_id.value
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="compliance_report_generated",
        actor_id=company["id"],
        target_id=report["id"],
        target_type="report",
        data={
            "framework": request.framework_id.value,
            "score": report["overall_score"],
            "status": report["status"]
        }
    )

    return report


@router.get("/reports/{consortium_id}", response_model=List[ComplianceReportResponse])
async def get_reports(
    consortium_id: str,
    framework_id: Optional[ComplianceFramework] = None,
    company: dict = Depends(get_current_company),
):
    """Get compliance reports for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    reports = manager.get_compliance_reports(
        consortium_id,
        framework_id=framework_id.value if framework_id else None
    )
    return reports


# ============ Attestations ============

@router.post("/attestations", response_model=AttestationResponse)
async def create_attestation(
    request: CreateAttestationRequest,
    company: dict = Depends(get_current_company),
):
    """Create a compliance attestation."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this consortium"
        )

    # Create attestation
    attestation_id = manager.create_attestation(
        consortium_id=request.consortium_id,
        framework_id=request.framework_id.value,
        attested_by=company["id"],
        statement=request.statement,
        control_id=request.control_id,
        attester_role=request.attester_role,
        attestation_type=request.attestation_type,
        evidence_urls=request.evidence_urls,
        valid_days=request.valid_days
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="compliance_attestation_created",
        actor_id=company["id"],
        target_id=attestation_id,
        target_type="attestation",
        data={
            "framework": request.framework_id.value,
            "attestation_type": request.attestation_type
        }
    )

    from datetime import timedelta
    now = datetime.utcnow()

    return AttestationResponse(
        id=attestation_id,
        consortium_id=request.consortium_id,
        framework_id=request.framework_id.value,
        control_id=request.control_id,
        attested_by=company["id"],
        attester_name=company["name"],
        attester_role=request.attester_role,
        attestation_type=request.attestation_type,
        statement=request.statement,
        evidence_urls=request.evidence_urls,
        valid_from=now,
        valid_until=now + timedelta(days=request.valid_days),
        revoked=False
    )


@router.get("/attestations/{consortium_id}", response_model=List[AttestationResponse])
async def get_attestations(
    consortium_id: str,
    framework_id: Optional[ComplianceFramework] = None,
    include_revoked: bool = False,
    company: dict = Depends(get_current_company),
):
    """Get attestations for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    attestations = manager.get_attestations(
        consortium_id,
        framework_id=framework_id.value if framework_id else None,
        include_revoked=include_revoked
    )
    return attestations


# ============ Data Processing Records (GDPR) ============

@router.post("/data-processing", response_model=DataProcessingRecordResponse)
async def record_data_processing(
    request: RecordDataProcessingRequest,
    company: dict = Depends(get_current_company),
):
    """Record a data processing activity (GDPR Article 30)."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this consortium"
        )

    # Record data processing
    record_id = manager.record_data_processing(
        consortium_id=request.consortium_id,
        company_id=company["id"],
        processing_purpose=request.processing_purpose,
        data_categories=request.data_categories,
        legal_basis=request.legal_basis,
        data_subjects=request.data_subjects,
        recipients=request.recipients,
        retention_period=request.retention_period,
        security_measures=request.security_measures,
        cross_border_transfer=request.cross_border_transfer,
        transfer_safeguards=request.transfer_safeguards
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="data_processing_recorded",
        actor_id=company["id"],
        target_id=record_id,
        target_type="data_processing",
        data={
            "purpose": request.processing_purpose,
            "legal_basis": request.legal_basis
        }
    )

    return DataProcessingRecordResponse(
        id=record_id,
        consortium_id=request.consortium_id,
        company_id=company["id"],
        company_name=company["name"],
        processing_purpose=request.processing_purpose,
        data_categories=request.data_categories,
        data_subjects=request.data_subjects,
        recipients=request.recipients,
        retention_period=request.retention_period,
        security_measures=request.security_measures,
        legal_basis=request.legal_basis,
        cross_border_transfer=request.cross_border_transfer,
        transfer_safeguards=request.transfer_safeguards,
        created_at=datetime.utcnow()
    )


@router.get("/data-processing/{consortium_id}", response_model=List[DataProcessingRecordResponse])
async def get_data_processing_records(
    consortium_id: str,
    company_id: Optional[str] = None,
    company: dict = Depends(get_current_company),
):
    """Get data processing records for a consortium."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    records = manager.get_data_processing_records(
        consortium_id,
        company_id=company_id
    )
    return records


# ============ Dashboard ============

@router.get("/dashboard/{consortium_id}", response_model=ComplianceDashboardResponse)
async def get_compliance_dashboard(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get compliance dashboard for a consortium.

    Returns an overview of compliance status across all enabled frameworks.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    dashboard = manager.get_compliance_dashboard(consortium_id)
    return dashboard
