"""API routes for Federated Inference (TIER 4).

This module provides REST endpoints for:
- Managing inference endpoints
- Submitting and tracking inference requests
- Managing federated models
- Registering and managing edge nodes
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .auth import get_current_company


# ============ Request Models ============

class CreateEndpointRequest(BaseModel):
    """Request to create an inference endpoint."""
    consortium_id: str
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    model_id: Optional[str] = None
    endpoint_type: str = Field(default="realtime", description="Type: realtime, batch, streaming")
    config: Optional[Dict[str, Any]] = None


class SubmitInferenceRequest(BaseModel):
    """Request to submit an inference request."""
    input_data: Dict[str, Any] = Field(..., description="Input data for prediction")
    priority: str = Field(default="normal", description="Priority: low, normal, high")
    encryption_key_id: Optional[str] = None


class CreateFederatedModelRequest(BaseModel):
    """Request to create a federated model."""
    consortium_id: str
    name: str = Field(..., min_length=1, max_length=100)
    model_type: str = Field(..., description="Type: linear_regression, logistic_regression, neural_network, xgboost")
    description: Optional[str] = None
    version: str = Field(default="1.0.0")
    config: Optional[Dict[str, Any]] = None


class RegisterEdgeNodeRequest(BaseModel):
    """Request to register an edge node."""
    name: str = Field(..., min_length=1, max_length=100)
    node_type: str = Field(default="on_premise", description="Type: on_premise, cloud, hybrid")
    location: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None


class DeployModelRequest(BaseModel):
    """Request to deploy a model to an edge node."""
    model_id: str


# ============ Response Models ============

class EndpointResponse(BaseModel):
    """Inference endpoint response."""
    id: str
    consortium_id: str
    company_id: str
    company_name: Optional[str]
    name: str
    description: Optional[str]
    model_id: Optional[str]
    model_name: Optional[str]
    endpoint_type: str
    status: str
    url: Optional[str]
    config: Dict[str, Any]
    request_count: int
    avg_latency_ms: float
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class InferenceRequestResponse(BaseModel):
    """Inference request response."""
    id: str
    endpoint_id: str
    requester_id: str
    requester_name: Optional[str]
    status: str
    priority: str
    input_hash: str
    encryption_key_id: Optional[str]
    created_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    latency_ms: Optional[float]


class InferenceResultResponse(BaseModel):
    """Inference result response."""
    request_id: str
    encrypted_output: str
    output_metadata: Dict[str, Any]
    confidence_scores: List[float]
    created_at: Optional[datetime]


class FederatedModelResponse(BaseModel):
    """Federated model response."""
    id: str
    consortium_id: str
    name: str
    description: Optional[str]
    model_type: str
    version: str
    status: str
    config: Dict[str, Any]
    metrics: Dict[str, Any]
    deployment_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class EdgeNodeResponse(BaseModel):
    """Edge node response."""
    id: str
    company_id: str
    company_name: Optional[str]
    name: str
    node_type: str
    location: Optional[str]
    status: str
    capabilities: Dict[str, Any]
    deployed_models: List[str]
    last_heartbeat: Optional[datetime]
    created_at: Optional[datetime]


class FederatedStatsResponse(BaseModel):
    """Federated inference statistics response."""
    total_endpoints: int
    active_endpoints: int
    total_requests: int
    completed_requests: int
    total_models: int
    deployed_models: int
    total_edge_nodes: int
    online_edge_nodes: int
    avg_latency_ms: float


# ============ Router ============

router = APIRouter(prefix="/federated", tags=["federated"])


# ============ Inference Endpoints ============

@router.post("/endpoints", response_model=EndpointResponse)
async def create_endpoint(
    request: CreateEndpointRequest,
    company: dict = Depends(get_current_company),
):
    """Create a new inference endpoint."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    endpoint = manager.create_inference_endpoint(
        consortium_id=request.consortium_id,
        company_id=company["id"],
        name=request.name,
        description=request.description,
        model_id=request.model_id,
        endpoint_type=request.endpoint_type,
        config=request.config
    )

    return endpoint


@router.get("/endpoints", response_model=List[EndpointResponse])
async def list_endpoints(
    company: dict = Depends(get_current_company),
    consortium_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """List inference endpoints."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    endpoints = manager.list_inference_endpoints(
        company_id=company["id"],
        consortium_id=consortium_id,
        status=status
    )

    return endpoints


@router.get("/endpoints/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific inference endpoint."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    endpoint = manager.get_inference_endpoint(endpoint_id)

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    if endpoint["company_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this endpoint")

    return endpoint


@router.delete("/endpoints/{endpoint_id}")
async def delete_endpoint(
    endpoint_id: str,
    company: dict = Depends(get_current_company),
):
    """Delete an inference endpoint."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    success = manager.delete_inference_endpoint(endpoint_id, company["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Endpoint not found or not authorized")

    return {"status": "deleted", "endpoint_id": endpoint_id}


# ============ Inference Requests ============

@router.post("/endpoints/{endpoint_id}/infer", response_model=InferenceRequestResponse)
async def submit_inference(
    endpoint_id: str,
    request: SubmitInferenceRequest,
    company: dict = Depends(get_current_company),
):
    """Submit an inference request."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify endpoint exists
    endpoint = manager.get_inference_endpoint(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    inference_request = manager.submit_inference_request(
        endpoint_id=endpoint_id,
        requester_id=company["id"],
        input_data=request.input_data,
        priority=request.priority,
        encryption_key_id=request.encryption_key_id
    )

    return inference_request


@router.get("/requests", response_model=List[InferenceRequestResponse])
async def list_inference_requests(
    company: dict = Depends(get_current_company),
    endpoint_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """List inference requests."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    requests = manager.list_inference_requests(
        requester_id=company["id"],
        endpoint_id=endpoint_id,
        status=status
    )

    return requests


@router.get("/requests/{request_id}", response_model=InferenceRequestResponse)
async def get_inference_request(
    request_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific inference request."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    req = manager.get_inference_request(request_id)

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req["requester_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this request")

    return req


@router.get("/requests/{request_id}/result", response_model=InferenceResultResponse)
async def get_inference_result(
    request_id: str,
    company: dict = Depends(get_current_company),
):
    """Get the result of an inference request."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify request ownership
    req = manager.get_inference_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req["requester_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = manager.get_inference_result(request_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not available yet")

    return result


# ============ Federated Models ============

@router.post("/models", response_model=FederatedModelResponse)
async def create_federated_model(
    request: CreateFederatedModelRequest,
    company: dict = Depends(get_current_company),
):
    """Create a new federated model."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    model = manager.create_federated_model(
        consortium_id=request.consortium_id,
        name=request.name,
        model_type=request.model_type,
        created_by=company["id"],
        description=request.description,
        version=request.version,
        config=request.config
    )

    return model


@router.get("/models", response_model=List[FederatedModelResponse])
async def list_federated_models(
    company: dict = Depends(get_current_company),
    consortium_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """List federated models."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    models = manager.list_federated_models(
        consortium_id=consortium_id,
        status=status
    )

    return models


@router.get("/models/{model_id}", response_model=FederatedModelResponse)
async def get_federated_model(
    model_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific federated model."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    model = manager.get_federated_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return model


# ============ Edge Nodes ============

@router.post("/nodes", response_model=EdgeNodeResponse)
async def register_edge_node(
    request: RegisterEdgeNodeRequest,
    company: dict = Depends(get_current_company),
):
    """Register a new edge node."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    node = manager.register_edge_node(
        company_id=company["id"],
        name=request.name,
        node_type=request.node_type,
        location=request.location,
        capabilities=request.capabilities
    )

    return node


@router.get("/nodes", response_model=List[EdgeNodeResponse])
async def list_edge_nodes(
    company: dict = Depends(get_current_company),
    status: Optional[str] = None,
):
    """List edge nodes for the current company."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    nodes = manager.list_edge_nodes(
        company_id=company["id"],
        status=status
    )

    return nodes


@router.get("/nodes/{node_id}", response_model=EdgeNodeResponse)
async def get_edge_node(
    node_id: str,
    company: dict = Depends(get_current_company),
):
    """Get a specific edge node."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    node = manager.get_edge_node(node_id)

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if node["company_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this node")

    return node


@router.post("/nodes/{node_id}/deploy", response_model=EdgeNodeResponse)
async def deploy_model_to_node(
    node_id: str,
    request: DeployModelRequest,
    company: dict = Depends(get_current_company),
):
    """Deploy a model to an edge node."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    node = manager.deploy_model_to_edge(
        node_id=node_id,
        model_id=request.model_id,
        company_id=company["id"]
    )

    if not node:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    return node


@router.post("/nodes/{node_id}/heartbeat")
async def update_node_heartbeat(
    node_id: str,
    company: dict = Depends(get_current_company),
):
    """Update edge node heartbeat."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())

    # Verify ownership
    node = manager.get_edge_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if node["company_id"] != company["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    manager.update_edge_heartbeat(node_id)

    return {"status": "ok", "node_id": node_id}


@router.delete("/nodes/{node_id}")
async def delete_edge_node(
    node_id: str,
    company: dict = Depends(get_current_company),
):
    """Delete an edge node."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    success = manager.delete_edge_node(node_id, company["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    return {"status": "deleted", "node_id": node_id}


# ============ Statistics ============

@router.get("/stats", response_model=FederatedStatsResponse)
async def get_federated_stats(
    company: dict = Depends(get_current_company),
):
    """Get federated inference statistics."""
    from .consortium import ConsortiumManager
    from .database import get_db_path

    manager = ConsortiumManager(get_db_path())
    stats = manager.get_federated_stats(company_id=company["id"])
    return stats
