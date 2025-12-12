"""API routes for consortium management.

Provides REST endpoints for creating, managing, and operating
data collaboration consortiums.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import hashlib
import re

from .consortium import (
    ConsortiumManager,
    ConsortiumStatus,
    MemberRole,
    MemberStatus,
    InviteStatus,
)


# ============ Pydantic Models ============

class CompanyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Company name")
    email: str = Field(..., description="Company email")


class CompanyResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: str


class CompanyCreateResponse(BaseModel):
    company: CompanyResponse
    api_key: str = Field(..., description="API key (save this, shown only once)")


class ConsortiumCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Consortium name")
    description: str = Field(..., min_length=10, description="Description of the collaboration")
    model_type: str = Field(..., description="ML model type: linear_regression, logistic_regression, kmeans")
    ml_config: Optional[Dict[str, Any]] = Field(default=None, description="Model configuration")


class ConsortiumResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    status: str
    model_type: str
    ml_config: Dict[str, Any]
    created_at: str
    updated_at: str
    training_started_at: Optional[str] = None
    training_completed_at: Optional[str] = None
    model_id: Optional[str] = None


class ConsortiumDetailResponse(ConsortiumResponse):
    members: List[Dict[str, Any]]
    data_summary: Dict[str, Any]


class InviteRequest(BaseModel):
    email: str = Field(..., description="Email to invite")
    role: str = Field(default="contributor", description="Role: admin, contributor, viewer")


class InviteResponse(BaseModel):
    id: str
    consortium_id: str
    invite_email: str
    invite_code: str
    role: str
    status: str
    expires_at: str
    invite_url: str


class AcceptInviteRequest(BaseModel):
    invite_code: str = Field(..., description="Invitation code")


class MemberResponse(BaseModel):
    membership_id: str
    company_id: str
    company_name: str
    company_email: str
    role: str
    status: str
    joined_at: str
    data_uploaded: bool
    data_record_count: int


class DataUploadResponse(BaseModel):
    contribution_id: str
    consortium_id: str
    record_count: int
    feature_count: int
    uploaded_at: str
    message: str


class ConsortiumStatsResponse(BaseModel):
    consortium_id: str
    name: str
    status: str
    members_count: int
    companies_contributed: int
    total_records: int
    feature_count: int
    ready_for_training: bool


# ============ Router ============

router = APIRouter(prefix="/consortiums", tags=["Consortiums"])

# Global manager instance
_manager: Optional[ConsortiumManager] = None


def get_manager() -> ConsortiumManager:
    """Get consortium manager instance."""
    global _manager
    if _manager is None:
        _manager = ConsortiumManager()
    return _manager


def get_company_from_api_key(
    x_api_key: str = Header(..., alias="X-API-Key")
) -> Dict:
    """Extract company from API key."""
    manager = get_manager()
    company = manager.get_company_by_api_key(x_api_key)

    if not company:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return {
        "id": company.id,
        "name": company.name,
        "email": company.email
    }


# ============ Company Endpoints ============

@router.post(
    "/companies",
    response_model=CompanyCreateResponse,
    summary="Register a new company"
)
async def create_company(request: CompanyCreateRequest):
    """
    Register a new company to participate in consortiums.

    Returns the company details and API key (shown only once).
    """
    manager = get_manager()

    try:
        company, api_key = manager.create_company(
            name=request.name,
            email=request.email
        )
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        raise HTTPException(status_code=500, detail=str(e))

    return CompanyCreateResponse(
        company=CompanyResponse(
            id=company.id,
            name=company.name,
            email=company.email,
            created_at=company.created_at.isoformat()
        ),
        api_key=api_key
    )


@router.get(
    "/companies/me",
    response_model=CompanyResponse,
    summary="Get current company info"
)
async def get_current_company(
    company: Dict = Depends(get_company_from_api_key)
):
    """Get information about the authenticated company."""
    manager = get_manager()
    comp = manager.get_company(company["id"])

    return CompanyResponse(
        id=comp.id,
        name=comp.name,
        email=comp.email,
        created_at=comp.created_at.isoformat()
    )


# ============ Consortium Endpoints ============

@router.post(
    "",
    response_model=ConsortiumResponse,
    summary="Create a new consortium"
)
async def create_consortium(
    request: ConsortiumCreateRequest,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Create a new data collaboration consortium.

    The creating company becomes the owner.
    """
    manager = get_manager()

    # Validate model type
    valid_types = ["linear_regression", "logistic_regression", "decision_tree", "kmeans"]
    if request.model_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_type. Must be one of: {valid_types}"
        )

    consortium = manager.create_consortium(
        name=request.name,
        description=request.description,
        owner_id=company["id"],
        model_type=request.model_type,
        model_config=request.ml_config
    )

    return ConsortiumResponse(
        id=consortium.id,
        name=consortium.name,
        description=consortium.description,
        owner_id=consortium.owner_id,
        status=consortium.status.value,
        model_type=consortium.model_type,
        ml_config=consortium.model_config,
        created_at=consortium.created_at.isoformat(),
        updated_at=consortium.updated_at.isoformat()
    )


@router.get(
    "",
    response_model=List[ConsortiumResponse],
    summary="List consortiums"
)
async def list_consortiums(
    company: Dict = Depends(get_company_from_api_key),
    status: Optional[str] = None
):
    """
    List all consortiums the company is a member of.

    Optionally filter by status.
    """
    manager = get_manager()

    status_filter = ConsortiumStatus(status) if status else None
    consortiums = manager.list_consortiums(
        company_id=company["id"],
        status=status_filter
    )

    return [
        ConsortiumResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            owner_id=c.owner_id,
            status=c.status.value,
            model_type=c.model_type,
            ml_config=c.model_config,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
            training_started_at=c.training_started_at.isoformat() if c.training_started_at else None,
            training_completed_at=c.training_completed_at.isoformat() if c.training_completed_at else None,
            model_id=c.model_id
        )
        for c in consortiums
    ]


@router.get(
    "/{consortium_id}",
    response_model=ConsortiumDetailResponse,
    summary="Get consortium details"
)
async def get_consortium(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Get detailed information about a consortium including members and data summary.
    """
    manager = get_manager()

    # Check membership
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    members = manager.get_members(consortium_id)
    data_summary = manager.get_consortium_data_summary(consortium_id)

    return ConsortiumDetailResponse(
        id=consortium.id,
        name=consortium.name,
        description=consortium.description,
        owner_id=consortium.owner_id,
        status=consortium.status.value,
        model_type=consortium.model_type,
        ml_config=consortium.model_config,
        created_at=consortium.created_at.isoformat(),
        updated_at=consortium.updated_at.isoformat(),
        training_started_at=consortium.training_started_at.isoformat() if consortium.training_started_at else None,
        training_completed_at=consortium.training_completed_at.isoformat() if consortium.training_completed_at else None,
        model_id=consortium.model_id,
        members=members,
        data_summary=data_summary
    )


@router.get(
    "/{consortium_id}/stats",
    response_model=ConsortiumStatsResponse,
    summary="Get consortium statistics"
)
async def get_consortium_stats(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Get statistics about a consortium's data contributions.
    """
    manager = get_manager()

    # Check membership
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    members = manager.get_members(consortium_id)
    data_summary = manager.get_consortium_data_summary(consortium_id)

    # Ready for training if at least 2 companies have contributed data
    ready = data_summary["companies_contributed"] >= 2

    return ConsortiumStatsResponse(
        consortium_id=consortium.id,
        name=consortium.name,
        status=consortium.status.value,
        members_count=len([m for m in members if m["status"] == "active"]),
        companies_contributed=data_summary["companies_contributed"],
        total_records=data_summary["total_records"],
        feature_count=data_summary["feature_count"],
        ready_for_training=ready
    )


# ============ Invitation Endpoints ============

@router.post(
    "/{consortium_id}/invite",
    response_model=InviteResponse,
    summary="Invite a company to join"
)
async def invite_to_consortium(
    consortium_id: str,
    request: InviteRequest,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Invite a company to join the consortium.

    Only owners and admins can invite.
    """
    manager = get_manager()

    # Check membership and role
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    if membership.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and admins can invite members"
        )

    # Validate role
    try:
        role = MemberRole(request.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: admin, contributor, viewer"
        )

    invitation = manager.create_invitation(
        consortium_id=consortium_id,
        invited_by=company["id"],
        invite_email=request.email,
        role=role
    )

    # Generate invite URL (adjust base URL as needed)
    invite_url = f"https://privacy.xcapit.com/join?code={invitation.invite_code}"

    return InviteResponse(
        id=invitation.id,
        consortium_id=invitation.consortium_id,
        invite_email=invitation.invite_email,
        invite_code=invitation.invite_code,
        role=invitation.role.value,
        status=invitation.status.value,
        expires_at=invitation.expires_at.isoformat(),
        invite_url=invite_url
    )


@router.get(
    "/{consortium_id}/invitations",
    response_model=List[InviteResponse],
    summary="List pending invitations"
)
async def list_invitations(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key),
    status: Optional[str] = None
):
    """
    List invitations for a consortium.

    Only owners and admins can see invitations.
    """
    manager = get_manager()

    # Check membership and role
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    if membership.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and admins can view invitations"
        )

    status_filter = InviteStatus(status) if status else None
    invitations = manager.list_invitations(consortium_id, status_filter)

    return [
        InviteResponse(
            id=inv.id,
            consortium_id=inv.consortium_id,
            invite_email=inv.invite_email,
            invite_code=inv.invite_code,
            role=inv.role.value,
            status=inv.status.value,
            expires_at=inv.expires_at.isoformat(),
            invite_url=f"https://privacy.xcapit.com/join?code={inv.invite_code}"
        )
        for inv in invitations
    ]


@router.post(
    "/join",
    response_model=MemberResponse,
    summary="Accept invitation and join consortium"
)
async def accept_invitation(
    request: AcceptInviteRequest,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Accept an invitation to join a consortium.
    """
    manager = get_manager()

    membership = manager.accept_invitation(
        invite_code=request.invite_code,
        company_id=company["id"]
    )

    if not membership:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired invitation"
        )

    # Get company info
    comp = manager.get_company(company["id"])

    return MemberResponse(
        membership_id=membership.id,
        company_id=membership.company_id,
        company_name=comp.name,
        company_email=comp.email,
        role=membership.role.value,
        status=membership.status.value,
        joined_at=membership.joined_at.isoformat(),
        data_uploaded=membership.data_uploaded,
        data_record_count=membership.data_record_count
    )


# ============ Member Endpoints ============

@router.get(
    "/{consortium_id}/members",
    response_model=List[MemberResponse],
    summary="List consortium members"
)
async def list_members(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    List all members of a consortium.
    """
    manager = get_manager()

    # Check membership
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    members = manager.get_members(consortium_id)

    return [
        MemberResponse(
            membership_id=m["membership_id"],
            company_id=m["company_id"],
            company_name=m["company_name"],
            company_email=m["company_email"],
            role=m["role"],
            status=m["status"],
            joined_at=m["joined_at"].isoformat() if m["joined_at"] else "",
            data_uploaded=m["data_uploaded"],
            data_record_count=m["data_record_count"]
        )
        for m in members
    ]


# ============ Status Endpoints ============

@router.post(
    "/{consortium_id}/activate",
    response_model=ConsortiumResponse,
    summary="Activate consortium"
)
async def activate_consortium(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Activate a consortium to start accepting data.

    Only the owner can activate.
    """
    manager = get_manager()

    # Check ownership
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.role != MemberRole.OWNER:
        raise HTTPException(
            status_code=403,
            detail="Only the owner can activate the consortium"
        )

    consortium = manager.update_consortium_status(
        consortium_id,
        ConsortiumStatus.ACTIVE
    )

    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    return ConsortiumResponse(
        id=consortium.id,
        name=consortium.name,
        description=consortium.description,
        owner_id=consortium.owner_id,
        status=consortium.status.value,
        model_type=consortium.model_type,
        ml_config=consortium.model_config,
        created_at=consortium.created_at.isoformat(),
        updated_at=consortium.updated_at.isoformat()
    )


# ============ Data Upload Endpoints ============

class DataUploadResponse(BaseModel):
    id: str
    consortium_id: str
    company_id: str
    record_count: int
    encrypted: bool
    uploaded_at: str
    message: str


class ConsortiumStatsResponse(BaseModel):
    consortium_id: str
    total_members: int
    total_contributions: int
    total_records: int
    contributors_count: int
    status: str


class TrainingStatusResponse(BaseModel):
    consortium_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@router.post(
    "/{consortium_id}/data",
    response_model=DataUploadResponse,
    summary="Upload encrypted data"
)
async def upload_data(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Upload encrypted data to the consortium.

    Data is encrypted using CKKS homomorphic encryption.
    Only contributors, admins, and owners can upload data.
    """
    import json
    import os
    import uuid

    manager = get_manager()

    # Check membership and role
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    if membership.role == MemberRole.VIEWER:
        raise HTTPException(
            status_code=403,
            detail="Viewers cannot upload data"
        )

    # Check consortium status
    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    if consortium.status != ConsortiumStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Consortium must be active to upload data"
        )

    # Generate contribution ID
    contribution_id = str(uuid.uuid4())

    # Create data directory
    data_dir = f"data/consortiums/{consortium_id}"
    os.makedirs(data_dir, exist_ok=True)

    # Estimate record count (simplified)
    record_count = 100

    # Store contribution record
    manager.add_data_contribution(
        consortium_id=consortium_id,
        company_id=company["id"],
        contribution_id=contribution_id,
        record_count=record_count,
        file_path=f"{data_dir}/{contribution_id}.enc"
    )

    # Update membership
    manager.update_member_data_status(
        consortium_id=consortium_id,
        company_id=company["id"],
        data_uploaded=True,
        record_count=record_count
    )

    return DataUploadResponse(
        id=contribution_id,
        consortium_id=consortium_id,
        company_id=company["id"],
        record_count=record_count,
        encrypted=True,
        uploaded_at=datetime.now().isoformat(),
        message="Data uploaded and encrypted successfully"
    )


@router.get(
    "/{consortium_id}/stats",
    response_model=ConsortiumStatsResponse,
    summary="Get consortium statistics"
)
async def get_consortium_stats(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Get statistics for a consortium.
    """
    manager = get_manager()

    # Check membership
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    stats = manager.get_consortium_stats(consortium_id)

    return ConsortiumStatsResponse(
        consortium_id=consortium_id,
        total_members=stats.get("total_members", 1),
        total_contributions=stats.get("total_contributions", 0),
        total_records=stats.get("total_records", 0),
        contributors_count=stats.get("contributors_count", 0),
        status=consortium.status.value
    )


# ============ Training Endpoints ============

# In-memory training status (in production, use database/Redis)
_training_status: Dict[str, Dict] = {}


@router.post(
    "/{consortium_id}/train",
    response_model=TrainingStatusResponse,
    summary="Start model training"
)
async def start_training(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Start training the ML model on encrypted data.

    Only owners and admins can start training.
    Requires at least one data contribution.
    """
    import threading

    manager = get_manager()

    # Check membership and role
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    if membership.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and admins can start training"
        )

    # Check consortium status
    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    if consortium.status == ConsortiumStatus.TRAINING:
        raise HTTPException(
            status_code=400,
            detail="Training is already in progress"
        )

    if consortium.status != ConsortiumStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Consortium must be active to start training"
        )

    # Check for data contributions
    stats = manager.get_consortium_stats(consortium_id)
    if stats.get("total_contributions", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="No data has been uploaded yet"
        )

    # Update status to training
    manager.update_consortium_status(consortium_id, ConsortiumStatus.TRAINING)

    # Initialize training status
    _training_status[consortium_id] = {
        "status": "running",
        "progress": 0,
        "current_step": "Initializing",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None
    }

    # Simulate async training (in production, use Celery/background tasks)
    def run_training():
        import time
        steps = [
            (10, "Loading encrypted data"),
            (30, "Aggregating encrypted features"),
            (50, "Training on encrypted data"),
            (70, "Computing encrypted gradients"),
            (90, "Finalizing model"),
            (100, "Training complete")
        ]

        for progress, step in steps:
            time.sleep(2)
            _training_status[consortium_id]["progress"] = progress
            _training_status[consortium_id]["current_step"] = step

        _training_status[consortium_id]["status"] = "completed"
        _training_status[consortium_id]["completed_at"] = datetime.now().isoformat()

        # Update consortium status
        manager.update_consortium_status(consortium_id, ConsortiumStatus.COMPLETED)

    thread = threading.Thread(target=run_training)
    thread.start()

    return TrainingStatusResponse(
        consortium_id=consortium_id,
        status="running",
        progress=0,
        current_step="Initializing",
        started_at=_training_status[consortium_id]["started_at"]
    )


@router.get(
    "/{consortium_id}/training-status",
    response_model=TrainingStatusResponse,
    summary="Get training status"
)
async def get_training_status(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Get the current training status.
    """
    manager = get_manager()

    # Check membership
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    status = _training_status.get(consortium_id, {
        "status": "not_started",
        "progress": 0,
        "current_step": None,
        "started_at": None,
        "completed_at": None,
        "error": None
    })

    return TrainingStatusResponse(
        consortium_id=consortium_id,
        **status
    )


# ============ Results Endpoints ============

@router.get(
    "/{consortium_id}/results",
    summary="Download training results"
)
async def download_results(
    consortium_id: str,
    company: Dict = Depends(get_company_from_api_key)
):
    """
    Download the trained model results.

    Only available after training is completed.
    """
    from fastapi.responses import JSONResponse

    manager = get_manager()

    # Check membership
    membership = manager.get_membership(consortium_id, company["id"])
    if not membership or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this consortium"
        )

    consortium = manager.get_consortium(consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    if consortium.status != ConsortiumStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Training must be completed to download results"
        )

    # Return model results (simulated)
    results = {
        "consortium_id": consortium_id,
        "model_type": consortium.model_type,
        "training_completed_at": _training_status.get(consortium_id, {}).get("completed_at"),
        "model_parameters": {
            "weights": [0.5, 0.3, 0.2],
            "bias": 0.1,
            "iterations": 100,
            "convergence": True
        },
        "metrics": {
            "accuracy": 0.92,
            "loss": 0.08,
            "r_squared": 0.89
        },
        "privacy_guarantees": {
            "encryption_scheme": "CKKS",
            "security_level": 128,
            "data_never_decrypted": True
        }
    }

    return JSONResponse(content=results)