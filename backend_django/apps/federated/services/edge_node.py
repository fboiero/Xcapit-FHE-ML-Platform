"""
Edge node management service.

Handles:
- Node registration and heartbeats
- Model deployment to nodes
- Node status management
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.core.models import Company
    from apps.federated.models import EdgeNode, FederatedModel

logger = logging.getLogger(__name__)


class EdgeNodeService(BaseService):
    """
    Service for managing edge nodes.

    Handles:
    - Node registration and configuration
    - Heartbeat processing
    - Model deployment/undeployment
    - Node health monitoring
    """

    # Node is considered offline after this many seconds without heartbeat
    OFFLINE_THRESHOLD_SECONDS = 300  # 5 minutes

    def register_node(
        self,
        company: Company,
        name: str,
        node_type: str,
        capabilities: dict[str, Any] | None = None,
    ) -> ServiceResult[EdgeNode]:
        """
        Register a new edge node.

        Args:
            company: Owner company
            name: Node name
            node_type: Type of node (cpu, gpu, tpu)
            capabilities: Hardware/software capabilities

        Returns:
            ServiceResult with created node
        """
        from apps.federated.models import EdgeNode

        with transaction.atomic():
            node = EdgeNode.objects.create(
                company=company,
                name=name,
                node_type=node_type,
                capabilities=capabilities or {},
                status=EdgeNode.Status.OFFLINE,
            )

            logger.info(f"Registered edge node {node.id} for company {company.id}")

            return ServiceResult.ok(node)

    def record_heartbeat(self, node: EdgeNode) -> ServiceResult[EdgeNode]:
        """
        Record a heartbeat from a node.

        Args:
            node: The node sending heartbeat

        Returns:
            ServiceResult with updated node
        """
        from apps.federated.models import EdgeNode

        node.last_heartbeat = timezone.now()

        # Update status to online if it was offline
        if node.status == EdgeNode.Status.OFFLINE:
            node.status = EdgeNode.Status.ONLINE

        node.save(update_fields=["last_heartbeat", "status", "updated_at"])

        logger.debug(f"Heartbeat recorded for node {node.id}")

        return ServiceResult.ok(node)

    def deploy_model_to_node(
        self,
        node: EdgeNode,
        model: FederatedModel,
    ) -> ServiceResult[EdgeNode]:
        """
        Deploy a federated model to an edge node.

        Args:
            node: Target node
            model: Model to deploy

        Returns:
            ServiceResult with updated node
        """
        from apps.federated.models import FederatedModel

        # Validate model status
        if model.status not in [
            FederatedModel.Status.READY,
            FederatedModel.Status.DEPLOYED,
        ]:
            return ServiceResult.fail(
                "Model is not ready for deployment",
                error_code="invalid_status",
            )

        # Check if already deployed
        if node.deployed_models.filter(id=model.id).exists():
            return ServiceResult.fail(
                "Model is already deployed to this node",
                error_code="already_deployed",
            )

        # Check node capacity (optional, based on capabilities)
        max_models = node.capabilities.get("max_models", 10)
        if node.deployed_models.count() >= max_models:
            return ServiceResult.fail(
                f"Node has reached maximum capacity ({max_models} models)",
                error_code="capacity_exceeded",
            )

        node.deployed_models.add(model)

        logger.info(f"Deployed model {model.id} to node {node.id}")

        return ServiceResult.ok(node)

    def undeploy_model_from_node(
        self,
        node: EdgeNode,
        model: FederatedModel,
    ) -> ServiceResult[EdgeNode]:
        """
        Remove a model from an edge node.

        Args:
            node: Target node
            model: Model to remove

        Returns:
            ServiceResult with updated node
        """
        # Check if deployed
        if not node.deployed_models.filter(id=model.id).exists():
            return ServiceResult.fail(
                "Model is not deployed to this node",
                error_code="not_deployed",
            )

        node.deployed_models.remove(model)

        logger.info(f"Undeployed model {model.id} from node {node.id}")

        return ServiceResult.ok(node)

    def update_node_status(self, node: EdgeNode) -> EdgeNode:
        """
        Update node status based on heartbeat.

        Args:
            node: The node to check

        Returns:
            Updated node
        """
        from apps.federated.models import EdgeNode

        if node.last_heartbeat is None:
            return node

        threshold = timezone.now() - timedelta(seconds=self.OFFLINE_THRESHOLD_SECONDS)

        if node.last_heartbeat < threshold and node.status == EdgeNode.Status.ONLINE:
            node.status = EdgeNode.Status.OFFLINE
            node.save(update_fields=["status", "updated_at"])
            logger.info(f"Node {node.id} marked as offline (no heartbeat)")

        return node

    def get_online_nodes(self, company: Company) -> list[EdgeNode]:
        """
        Get all online nodes for a company.

        Args:
            company: The company to get nodes for

        Returns:
            List of online nodes
        """
        from apps.federated.models import EdgeNode

        # First, update status of all nodes
        nodes = EdgeNode.objects.filter(company=company)
        for node in nodes:
            self.update_node_status(node)

        # Return online nodes
        return list(
            EdgeNode.objects.filter(
                company=company,
                status=EdgeNode.Status.ONLINE,
            )
        )

    def get_node_health(self, node: EdgeNode) -> dict[str, Any]:
        """
        Get health information for a node.

        Args:
            node: The node to check

        Returns:
            Dictionary with health information
        """
        # Update status first
        node = self.update_node_status(node)

        # Calculate uptime (simulated)
        uptime_hours = 0
        if node.last_heartbeat:
            uptime_hours = min(
                (timezone.now() - node.created_at).total_seconds() / 3600,
                720,  # Max 30 days
            )

        return {
            "id": str(node.id),
            "name": node.name,
            "status": node.status,
            "node_type": node.node_type,
            "last_heartbeat": (
                node.last_heartbeat.isoformat() if node.last_heartbeat else None
            ),
            "uptime_hours": round(uptime_hours, 2),
            "deployed_models_count": node.deployed_models.count(),
            "capabilities": node.capabilities,
            "is_healthy": node.status == node.Status.ONLINE,
        }

    def cleanup_stale_nodes(self, company: Company | None = None) -> ServiceResult[int]:
        """
        Mark stale nodes as offline.

        Args:
            company: Optional company filter

        Returns:
            ServiceResult with count of nodes updated
        """
        from apps.federated.models import EdgeNode

        threshold = timezone.now() - timedelta(seconds=self.OFFLINE_THRESHOLD_SECONDS)

        queryset = EdgeNode.objects.filter(
            status=EdgeNode.Status.ONLINE,
            last_heartbeat__lt=threshold,
        )

        if company:
            queryset = queryset.filter(company=company)

        count = queryset.count()
        queryset.update(status=EdgeNode.Status.OFFLINE)

        if count > 0:
            logger.info(f"Marked {count} stale nodes as offline")

        return ServiceResult.ok(count)
