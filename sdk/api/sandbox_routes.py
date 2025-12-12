"""API routes for Sandbox Mode (TIER 3).

This module provides REST endpoints for:
- Creating and managing sandbox environments
- Generating synthetic datasets
- Running experiments
- Managing sandbox templates
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .auth import get_current_company


# ============ Request Models ============

class CreateSandboxRequest(BaseModel):
    """Request to create a sandbox environment."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    template_id: Optional[str] = None
    industry: Optional[str] = None
    expires_days: int = Field(default=7, ge=1, le=30)


class GenerateDatasetRequest(BaseModel):
    """Request to generate a synthetic dataset."""
    name: str = Field(..., min_length=1, max_length=100)
    dataset_type: str = Field(..., description="Type of dataset: transactions, applications, customers, patients, generic")
    record_count: int = Field(default=1000, ge=100, le=100000)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class CreateExperimentRequest(BaseModel):
    """Request to create an experiment."""
    name: str = Field(..., min_length=1, max_length=100)
    experiment_type: str = Field(..., description="Type: training, evaluation, clustering, encryption_benchmark")
    model_type: Optional[str] = None
    dataset_id: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


# ============ Response Models ============

class SandboxResponse(BaseModel):
    """Sandbox environment response."""
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    owner_name: Optional[str]
    template_type: str
    industry: Optional[str]
    status: str
    created_at: Optional[datetime]
    expires_at: Optional[datetime]
    config: Dict[str, Any]
    dataset_count: int
    experiment_count: int


class DatasetResponse(BaseModel):
    """Synthetic dataset response."""
    id: str
    sandbox_id: str
    name: str
    description: Optional[str]
    dataset_type: str
    industry: Optional[str]
    record_count: int
    feature_count: int
    features: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    created_at: Optional[datetime]


class DatasetDetailResponse(DatasetResponse):
    """Detailed dataset response with preview."""
    data_preview: List[Dict[str, Any]]


class ExperimentResponse(BaseModel):
    """Experiment response."""
    id: str
    sandbox_id: str
    name: str
    description: Optional[str]
    experiment_type: str
    model_type: Optional[str]
    dataset_id: Optional[str]
    dataset_name: Optional[str]
    status: str
    config: Dict[str, Any]
    results: Dict[str, Any]
    created_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class TemplateResponse(BaseModel):
    """Sandbox template response."""
    id: str
    name: str
    description: Optional[str]
    industry: Optional[str]
    template_type: str
    datasets: List[Dict[str, Any]]
    experiments: List[Dict[str, Any]]


class SandboxStatsResponse(BaseModel):
    """Sandbox statistics response."""
    total_sandboxes: int
    active_sandboxes: int
    total_datasets: int
    total_experiments: int
    completed_experiments: int


# ============ Router ============

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


# ============ Templates ============

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    industry: Optional[str] = None,
):
    """Get available sandbox templates."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    templates = manager.list_sandbox_templates(industry=industry)
    return templates


# ============ Sandboxes ============

@router.post("/environments", response_model=SandboxResponse)
async def create_sandbox(
    request: CreateSandboxRequest,
    company: dict = Depends(get_current_company),
):
    """Create a new sandbox environment."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    sandbox = manager.create_sandbox(
        name=request.name,
        owner_id=company["id"],
        description=request.description,
        template_id=request.template_id,
        industry=request.industry,
        expires_days=request.expires_days
    )

    return sandbox


@router.get("/environments", response_model=List[SandboxResponse])
async def list_sandboxes(
    company: dict = Depends(get_current_company),
    status: Optional[str] = None,
):
    """List sandbox environments for the current company."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    sandboxes = manager.list_sandboxes(owner_id=company["id"], status=status)

    # Add counts for each sandbox
    result = []
    for s in sandboxes:
        sandbox = manager.get_sandbox(s["id"])
        if sandbox:
            result.append(sandbox)

    return result


@router.get("/environments/{sandbox_id}", response_model=SandboxResponse)
async def get_sandbox(
    sandbox_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific sandbox environment."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    sandbox = manager.get_sandbox(sandbox_id)

    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    if sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this sandbox")

    return sandbox


@router.delete("/environments/{sandbox_id}")
async def delete_sandbox(
    sandbox_id: str,
    company: dict = Depends(get_current_company),
):
    """Delete a sandbox environment."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    success = manager.delete_sandbox(sandbox_id, company["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Sandbox not found or not authorized")

    return {"status": "deleted", "sandbox_id": sandbox_id}


# ============ Datasets ============

@router.post("/environments/{sandbox_id}/datasets", response_model=DatasetDetailResponse)
async def generate_dataset(
    sandbox_id: str,
    request: GenerateDatasetRequest,
    company: dict = Depends(get_current_company),
):
    """Generate a synthetic dataset in the sandbox."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify sandbox ownership
    sandbox = manager.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    if sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    dataset = manager.generate_synthetic_dataset(
        sandbox_id=sandbox_id,
        name=request.name,
        dataset_type=request.dataset_type,
        record_count=request.record_count,
        created_by=company["id"],
        description=request.description,
        config=request.config
    )

    return dataset


@router.get("/environments/{sandbox_id}/datasets", response_model=List[DatasetResponse])
async def list_datasets(
    sandbox_id: str,
    company: dict = Depends(get_current_company),
):
    """List datasets in a sandbox."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify sandbox ownership
    sandbox = manager.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    if sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    datasets = manager.list_datasets(sandbox_id)
    return datasets


@router.get("/datasets/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific dataset with preview."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    dataset = manager.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Verify ownership via sandbox
    sandbox = manager.get_sandbox(dataset["sandbox_id"])
    if not sandbox or sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return dataset


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    company: dict = Depends(get_current_company),
):
    """Delete a dataset."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    success = manager.delete_dataset(dataset_id, company["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found or not authorized")

    return {"status": "deleted", "dataset_id": dataset_id}


# ============ Experiments ============

@router.post("/environments/{sandbox_id}/experiments", response_model=ExperimentResponse)
async def create_experiment(
    sandbox_id: str,
    request: CreateExperimentRequest,
    company: dict = Depends(get_current_company),
):
    """Create a new experiment in the sandbox."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify sandbox ownership
    sandbox = manager.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    if sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    experiment = manager.create_experiment(
        sandbox_id=sandbox_id,
        name=request.name,
        experiment_type=request.experiment_type,
        created_by=company["id"],
        model_type=request.model_type,
        dataset_id=request.dataset_id,
        description=request.description,
        config=request.config
    )

    return experiment


@router.get("/environments/{sandbox_id}/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    sandbox_id: str,
    company: dict = Depends(get_current_company),
):
    """List experiments in a sandbox."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify sandbox ownership
    sandbox = manager.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    if sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    experiments = manager.list_experiments(sandbox_id)
    return experiments


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific experiment."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    experiment = manager.get_experiment(experiment_id)

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Verify ownership via sandbox
    sandbox = manager.get_sandbox(experiment["sandbox_id"])
    if not sandbox or sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return experiment


@router.post("/experiments/{experiment_id}/run", response_model=ExperimentResponse)
async def run_experiment(
    experiment_id: str,
    company: dict = Depends(get_current_company),
):
    """Run an experiment."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify ownership
    experiment = manager.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    sandbox = manager.get_sandbox(experiment["sandbox_id"])
    if not sandbox or sandbox["owner_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if experiment["status"] not in ["pending", "failed"]:
        raise HTTPException(status_code=400, detail="Experiment cannot be run in current state")

    result = manager.run_experiment(experiment_id)
    return result


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(
    experiment_id: str,
    company: dict = Depends(get_current_company),
):
    """Delete an experiment."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    success = manager.delete_experiment(experiment_id, company["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found or not authorized")

    return {"status": "deleted", "experiment_id": experiment_id}


# ============ Statistics ============

@router.get("/stats", response_model=SandboxStatsResponse)
async def get_sandbox_stats(
    company: dict = Depends(get_current_company),
):
    """Get sandbox statistics for the current company."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    stats = manager.get_sandbox_stats(owner_id=company["id"])
    return stats
