"""API routes for consortium governance.

This module provides REST endpoints for:
- Contribution proofs
- Voting system
- Audit trail
- Reward distribution
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .auth import get_current_company


# ============ Pydantic Models ============

class ProposalType(str, Enum):
    """Types of governance proposals."""
    ADD_MEMBER = "add_member"
    REMOVE_MEMBER = "remove_member"
    CHANGE_MODEL = "change_model"
    START_TRAINING = "start_training"
    DISTRIBUTE_REWARDS = "distribute_rewards"
    UPDATE_CONFIG = "update_config"
    DISSOLVE = "dissolve"


class ProposalStatus(str, Enum):
    """Status of a proposal."""
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class AuditEventType(str, Enum):
    """Types of audit events."""
    CONSORTIUM_CREATED = "consortium_created"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_REMOVED = "member_removed"
    DATA_CONTRIBUTED = "data_contributed"
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_VOTED = "proposal_voted"
    PROPOSAL_EXECUTED = "proposal_executed"
    REWARDS_DISTRIBUTED = "rewards_distributed"
    CONFIG_UPDATED = "config_updated"


# Request Models
class RecordContributionRequest(BaseModel):
    """Request to record a contribution proof."""
    consortium_id: str
    record_count: int = Field(..., gt=0, description="Number of records contributed")
    feature_count: int = Field(..., gt=0, description="Number of features")
    data_hash: str = Field(..., description="Hash of encrypted data")
    checksum: str = Field(..., description="Checksum of the data blob")


class CreateProposalRequest(BaseModel):
    """Request to create a proposal."""
    consortium_id: str
    proposal_type: ProposalType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    data: Optional[Dict[str, Any]] = Field(default=None, description="Proposal-specific data")


class VoteRequest(BaseModel):
    """Request to cast a vote."""
    proposal_id: str
    support: bool = Field(..., description="True for yes, False for no")
    comment: Optional[str] = Field(default=None, max_length=500)


class DistributeRewardsRequest(BaseModel):
    """Request to distribute rewards."""
    consortium_id: str
    amount: float = Field(..., gt=0, description="Amount to distribute (in ETH)")


# Response Models
class ContributionProof(BaseModel):
    """Contribution proof response."""
    id: str
    consortium_id: str
    contributor_id: str
    contributor_name: str
    record_count: int
    feature_count: int
    data_hash: str
    checksum: str
    timestamp: datetime
    verified: bool
    blockchain_tx: Optional[str] = None


class Proposal(BaseModel):
    """Proposal response."""
    id: str
    consortium_id: str
    proposal_type: ProposalType
    title: str
    description: str
    proposer_id: str
    proposer_name: str
    status: ProposalStatus
    data: Optional[Dict[str, Any]]
    yes_votes: int
    no_votes: int
    total_voters: int
    voting_weight_yes: int
    voting_weight_no: int
    created_at: datetime
    expires_at: datetime
    executed_at: Optional[datetime]
    blockchain_tx: Optional[str] = None


class Vote(BaseModel):
    """Vote response."""
    id: str
    proposal_id: str
    voter_id: str
    voter_name: str
    support: bool
    weight: int
    comment: Optional[str]
    voted_at: datetime


class AuditEvent(BaseModel):
    """Audit event response."""
    id: str
    consortium_id: str
    event_type: AuditEventType
    actor_id: str
    actor_name: str
    target_id: Optional[str]
    target_type: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    blockchain_tx: Optional[str] = None
    previous_hash: Optional[str] = None


class MemberContribution(BaseModel):
    """Member contribution summary."""
    member_id: str
    member_name: str
    total_records: int
    contribution_weight: float  # Percentage 0-100
    contributions_count: int
    last_contribution_at: Optional[datetime]


class RewardDistribution(BaseModel):
    """Reward distribution record."""
    id: str
    consortium_id: str
    total_amount: float
    distributed_at: datetime
    distributions: List[Dict[str, Any]]  # member_id, amount, weight
    blockchain_tx: Optional[str] = None


# ============ Router ============

router = APIRouter(prefix="/governance", tags=["governance"])


# ============ Contribution Proofs ============

@router.post("/contributions", response_model=ContributionProof)
async def record_contribution(
    request: RecordContributionRequest,
    company: dict = Depends(get_current_company),
):
    """Record a contribution proof for data uploaded to a consortium.

    This creates an immutable record of the contribution that can be
    verified on-chain. The actual data is never stored on blockchain,
    only the hash and metadata.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is a member of the consortium
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this consortium"
        )

    # Record contribution in local DB
    contribution_id = manager.record_contribution_proof(
        consortium_id=request.consortium_id,
        company_id=company["id"],
        record_count=request.record_count,
        feature_count=request.feature_count,
        data_hash=request.data_hash,
        checksum=request.checksum,
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="data_contributed",
        actor_id=company["id"],
        target_id=contribution_id,
        data={
            "record_count": request.record_count,
            "feature_count": request.feature_count,
            "data_hash": request.data_hash,
        }
    )

    return ContributionProof(
        id=contribution_id,
        consortium_id=request.consortium_id,
        contributor_id=company["id"],
        contributor_name=company["name"],
        record_count=request.record_count,
        feature_count=request.feature_count,
        data_hash=request.data_hash,
        checksum=request.checksum,
        timestamp=datetime.utcnow(),
        verified=False,
        blockchain_tx=None,  # Will be set when recorded on-chain
    )


@router.get("/contributions/{consortium_id}", response_model=List[ContributionProof])
async def get_contributions(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get all contribution proofs for a consortium."""
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

    contributions = manager.get_contribution_proofs(consortium_id)
    return contributions


@router.get("/contributions/{consortium_id}/summary", response_model=List[MemberContribution])
async def get_contribution_summary(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get contribution summary per member for a consortium."""
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

    summary = manager.get_contribution_summary(consortium_id)
    return summary


# ============ Voting System ============

@router.post("/proposals", response_model=Proposal)
async def create_proposal(
    request: CreateProposalRequest,
    company: dict = Depends(get_current_company),
):
    """Create a new governance proposal."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify company is an active member
    membership = manager.get_membership(request.consortium_id, company["id"])
    if not membership or membership.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this consortium"
        )

    # Get consortium for voting duration
    consortium = manager.get_consortium(request.consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    # Create proposal
    proposal_id = manager.create_proposal(
        consortium_id=request.consortium_id,
        proposer_id=company["id"],
        proposal_type=request.proposal_type.value,
        title=request.title,
        description=request.description,
        data=request.data,
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="proposal_created",
        actor_id=company["id"],
        target_id=proposal_id,
        data={
            "proposal_type": request.proposal_type.value,
            "title": request.title,
        }
    )

    proposal = manager.get_proposal(proposal_id)
    return proposal


@router.get("/proposals/{consortium_id}", response_model=List[Proposal])
async def get_proposals(
    consortium_id: str,
    status_filter: Optional[ProposalStatus] = None,
    company: dict = Depends(get_current_company),
):
    """Get all proposals for a consortium."""
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

    proposals = manager.get_proposals(
        consortium_id,
        status_filter=status_filter.value if status_filter else None
    )
    return proposals


@router.get("/proposals/{consortium_id}/{proposal_id}", response_model=Proposal)
async def get_proposal(
    consortium_id: str,
    proposal_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific proposal."""
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

    proposal = manager.get_proposal(proposal_id)
    if not proposal or proposal.consortium_id != consortium_id:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return proposal


@router.post("/vote", response_model=Vote)
async def cast_vote(
    request: VoteRequest,
    company: dict = Depends(get_current_company),
):
    """Cast a vote on a proposal."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Get proposal
    proposal = manager.get_proposal(request.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Verify company is an active member
    membership = manager.get_membership(proposal.consortium_id, company["id"])
    if not membership or membership.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this consortium"
        )

    # Check proposal is still active
    if proposal.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is {proposal.status}, voting not allowed"
        )

    # Check voting deadline
    if datetime.utcnow() > proposal.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voting period has ended"
        )

    # Check if already voted
    existing_vote = manager.get_vote(request.proposal_id, company["id"])
    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already voted on this proposal"
        )

    # Calculate voting weight based on contributions
    contribution_summary = manager.get_member_contribution_summary(
        proposal.consortium_id, company["id"]
    )
    weight = max(1, contribution_summary.get("contribution_weight", 0))

    # Record vote
    vote_id = manager.record_vote(
        proposal_id=request.proposal_id,
        voter_id=company["id"],
        support=request.support,
        weight=weight,
        comment=request.comment,
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=proposal.consortium_id,
        event_type="proposal_voted",
        actor_id=company["id"],
        target_id=request.proposal_id,
        data={
            "support": request.support,
            "weight": weight,
        }
    )

    return Vote(
        id=vote_id,
        proposal_id=request.proposal_id,
        voter_id=company["id"],
        voter_name=company["name"],
        support=request.support,
        weight=weight,
        comment=request.comment,
        voted_at=datetime.utcnow(),
    )


@router.post("/proposals/{proposal_id}/execute")
async def execute_proposal(
    proposal_id: str,
    company: dict = Depends(get_current_company),
):
    """Execute a proposal after voting has ended."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Get proposal
    proposal = manager.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Verify company is a member
    membership = manager.get_membership(proposal.consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    # Check proposal status
    if proposal.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is already {proposal.status}"
        )

    # Check voting has ended
    if datetime.utcnow() < proposal.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voting period has not ended yet"
        )

    # Execute proposal
    result = manager.execute_proposal(proposal_id)

    # Record audit event
    manager.record_audit_event(
        consortium_id=proposal.consortium_id,
        event_type="proposal_executed",
        actor_id=company["id"],
        target_id=proposal_id,
        data={
            "passed": result["passed"],
            "yes_votes": result["yes_votes"],
            "no_votes": result["no_votes"],
        }
    )

    return {
        "proposal_id": proposal_id,
        "passed": result["passed"],
        "new_status": result["new_status"],
        "yes_votes": result["yes_votes"],
        "no_votes": result["no_votes"],
    }


@router.get("/proposals/{proposal_id}/votes", response_model=List[Vote])
async def get_votes(
    proposal_id: str,
    company: dict = Depends(get_current_company),
):
    """Get all votes for a proposal."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Get proposal
    proposal = manager.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Verify company is a member
    membership = manager.get_membership(proposal.consortium_id, company["id"])
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this consortium"
        )

    votes = manager.get_proposal_votes(proposal_id)
    return votes


# ============ Audit Trail ============

@router.get("/audit/{consortium_id}", response_model=List[AuditEvent])
async def get_audit_trail(
    consortium_id: str,
    event_type: Optional[AuditEventType] = None,
    limit: int = 100,
    offset: int = 0,
    company: dict = Depends(get_current_company),
):
    """Get audit trail for a consortium."""
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

    events = manager.get_audit_trail(
        consortium_id,
        event_type=event_type.value if event_type else None,
        limit=limit,
        offset=offset,
    )
    return events


@router.get("/audit/{consortium_id}/verify")
async def verify_audit_trail(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Verify the integrity of the audit trail."""
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

    is_valid = manager.verify_audit_trail(consortium_id)

    return {
        "consortium_id": consortium_id,
        "valid": is_valid,
        "verified_at": datetime.utcnow().isoformat(),
    }


# ============ Rewards ============

@router.post("/rewards/distribute", response_model=RewardDistribution)
async def distribute_rewards(
    request: DistributeRewardsRequest,
    company: dict = Depends(get_current_company),
):
    """Distribute rewards to consortium members based on contribution weights.

    Only the consortium owner can distribute rewards.
    """
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Get consortium
    consortium = manager.get_consortium(request.consortium_id)
    if not consortium:
        raise HTTPException(status_code=404, detail="Consortium not found")

    # Verify company is the owner
    if consortium.owner_id != company["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the consortium owner can distribute rewards"
        )

    # Calculate distributions based on contribution weights
    distributions = manager.calculate_reward_distribution(
        request.consortium_id,
        request.amount,
    )

    # Record distribution
    distribution_id = manager.record_reward_distribution(
        consortium_id=request.consortium_id,
        total_amount=request.amount,
        distributions=distributions,
    )

    # Record audit event
    manager.record_audit_event(
        consortium_id=request.consortium_id,
        event_type="rewards_distributed",
        actor_id=company["id"],
        target_id=distribution_id,
        data={
            "total_amount": request.amount,
            "recipient_count": len(distributions),
        }
    )

    return RewardDistribution(
        id=distribution_id,
        consortium_id=request.consortium_id,
        total_amount=request.amount,
        distributed_at=datetime.utcnow(),
        distributions=distributions,
        blockchain_tx=None,
    )


@router.get("/rewards/{consortium_id}", response_model=List[RewardDistribution])
async def get_reward_history(
    consortium_id: str,
    company: dict = Depends(get_current_company),
):
    """Get reward distribution history for a consortium."""
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

    history = manager.get_reward_distributions(consortium_id)
    return history
