"""
Views para la app de Federated.

ViewSets para gestionar modelos federados, endpoints de inferencia,
solicitudes de inferencia y nodos edge.
"""

from __future__ import annotations

import base64
import time

from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember, IsConsortiumMember

from .models import EdgeNode, FederatedModel, InferenceEndpoint, InferenceRequest, InferenceResult
from .serializers import (
    DeployModelSerializer,
    EdgeNodeCreateSerializer,
    EdgeNodeSerializer,
    FederatedModelCreateSerializer,
    FederatedModelSerializer,
    InferenceEndpointCreateSerializer,
    InferenceEndpointSerializer,
    InferencePredictSerializer,
    InferenceRequestCreateSerializer,
    InferenceRequestSerializer,
    InferenceResultSerializer,
)


# =============================================================================
# FederatedModel
# =============================================================================


class FederatedModelViewSet(viewsets.ModelViewSet):
    """
    CRUD para modelos federados.

    - list:        modelos filtrados por consortium_id.
    - create:      crear un modelo federado.
    - deploy:      marcar un modelo como desplegado (POST).
    - start_round: iniciar una ronda de entrenamiento federado (POST).
    """

    serializer_class = FederatedModelSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter models by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return FederatedModel.objects.filter(
                consortium_id=consortium_id,
            ).select_related("consortium")
        return FederatedModel.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return FederatedModelCreateSerializer
        return FederatedModelSerializer

    @action(detail=True, methods=["post"])
    def deploy(self, request, pk=None) -> Response:
        """
        Desplegar un modelo federado.

        Solo modelos con status 'ready' pueden ser desplegados.
        """
        model = self.get_object()

        if model.status != FederatedModel.Status.READY:
            return Response(
                {"detail": "Model must be ready before deployment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model.status = FederatedModel.Status.DEPLOYED
        model.save(update_fields=["status"])

        AuditLog.log(
            request,
            action="federated_model_deployed",
            resource_type="federated_model",
            resource_id=model.id,
            extra_data={"name": model.name, "version": model.version},
        )

        return Response({
            "detail": "Model deployed.",
            "model_id": str(model.id),
            "status": model.status,
        })

    @action(detail=True, methods=["post"])
    def start_round(self, request, pk=None) -> Response:
        """
        Iniciar una nueva ronda de entrenamiento federado.

        Cambia el estado del modelo a 'training' e inicia una ronda.
        """
        model = self.get_object()

        if model.status == FederatedModel.Status.TRAINING:
            return Response(
                {"detail": "Model is already training."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if model.status == FederatedModel.Status.ARCHIVED:
            return Response(
                {"detail": "Cannot start training on an archived model."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_round = model.metrics.get("current_round", 0) + 1

        model.status = FederatedModel.Status.TRAINING
        model.metrics = {
            **model.metrics,
            "current_round": current_round,
            "round_started_at": timezone.now().isoformat(),
        }
        model.save(update_fields=["status", "metrics"])

        AuditLog.log(
            request,
            action="federated_round_started",
            resource_type="federated_model",
            resource_id=model.id,
            extra_data={"round": current_round},
        )

        return Response({
            "detail": f"Training round {current_round} started.",
            "model_id": str(model.id),
            "status": model.status,
            "current_round": current_round,
        })

    @action(detail=True, methods=["post"])
    def train(self, request, pk=None) -> Response:
        """Iniciar entrenamiento federado (alias de start_round)."""
        model = self.get_object()

        if model.status == FederatedModel.Status.TRAINING:
            return Response(
                {"detail": "Model is already training."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model.status = FederatedModel.Status.TRAINING
        model.save(update_fields=["status"])

        return Response({
            "detail": "Federated training started.",
            "model_id": str(model.id),
            "status": model.status,
        })


# =============================================================================
# InferenceEndpoint
# =============================================================================


class InferenceEndpointViewSet(viewsets.ModelViewSet):
    """
    CRUD para endpoints de inferencia.

    Soporta filtros por consortium_id, status, endpoint_type.
    """

    serializer_class = InferenceEndpointSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "endpoint_type"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter endpoints by consortium or company."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return InferenceEndpoint.objects.filter(
                consortium_id=consortium_id
            ).select_related("company", "consortium", "model")

        user = self.request.user
        if user.company:
            return InferenceEndpoint.objects.filter(
                company=user.company
            ).select_related("company", "consortium", "model")
        return InferenceEndpoint.objects.none()

    def get_permissions(self):
        """Predict action uses get_object() for access control via queryset."""
        if self.action == "predict":
            return [IsAuthenticated(), IsCompanyMember()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return InferenceEndpointCreateSerializer
        return InferenceEndpointSerializer

    def perform_create(self, serializer):
        """Create endpoint and log event."""
        endpoint = serializer.save()

        # Generate URL
        endpoint.url = f"https://api.xcapit.io/inference/{endpoint.id}"
        endpoint.status = InferenceEndpoint.Status.ACTIVE
        endpoint.save()

        AuditLog.log(
            self.request,
            action="endpoint_created",
            resource_type="inference_endpoint",
            resource_id=endpoint.id,
            extra_data={
                "name": endpoint.name,
                "type": endpoint.endpoint_type,
            },
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def predict(self, request, pk=None) -> Response:
        """Ejecutar una prediccion a traves del endpoint."""
        endpoint = self.get_object()

        if endpoint.status != InferenceEndpoint.Status.ACTIVE:
            return Response(
                {"detail": "Endpoint is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InferenceRequestCreateSerializer(data={
            "endpoint_id": pk,
            **request.data,
        })
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        start_time = time.time()

        input_data = params["input_data"]
        inference_request = InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=request.user.company,
            input_hash=InferenceRequest.hash_input(input_data),
            encryption_key_id=params.get("encryption_key_id", ""),
            priority=params.get("priority", InferenceRequest.Priority.NORMAL),
        )

        inference_request.started_at = timezone.now()
        inference_request.status = InferenceRequest.Status.PROCESSING
        inference_request.save()

        n_samples = len(input_data)
        encrypted_output = base64.b64encode(
            f"encrypted_predictions_{n_samples}_samples".encode()
        ).decode()

        latency_ms = (time.time() - start_time) * 1000

        result = InferenceResult.objects.create(
            request=inference_request,
            encrypted_output=encrypted_output,
            output_metadata={
                "n_samples": n_samples,
                "model_version": endpoint.model.version if endpoint.model else "1.0.0",
            },
            confidence_scores=[0.95] * n_samples,
        )

        inference_request.status = InferenceRequest.Status.COMPLETED
        inference_request.completed_at = timezone.now()
        inference_request.latency_ms = latency_ms
        inference_request.save()

        endpoint.request_count += 1
        endpoint.total_latency_ms += latency_ms
        endpoint.save()

        return Response(InferencePredictSerializer({
            "request_id": inference_request.id,
            "encrypted_output": encrypted_output,
            "latency_ms": round(latency_ms, 2),
            "metadata": result.output_metadata,
        }).data)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None) -> Response:
        """Pausar un endpoint."""
        endpoint = self.get_object()

        if endpoint.status != InferenceEndpoint.Status.ACTIVE:
            return Response(
                {"detail": "Endpoint is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        endpoint.status = InferenceEndpoint.Status.PAUSED
        endpoint.save(update_fields=["status"])

        return Response({"detail": "Endpoint paused."})

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None) -> Response:
        """Reanudar un endpoint pausado."""
        endpoint = self.get_object()

        if endpoint.status != InferenceEndpoint.Status.PAUSED:
            return Response(
                {"detail": "Endpoint is not paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        endpoint.status = InferenceEndpoint.Status.ACTIVE
        endpoint.save(update_fields=["status"])

        return Response({"detail": "Endpoint resumed."})

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None) -> Response:
        """Obtener estadisticas del endpoint."""
        endpoint = self.get_object()

        return Response({
            "endpoint_id": str(endpoint.id),
            "name": endpoint.name,
            "status": endpoint.status,
            "request_count": endpoint.request_count,
            "avg_latency_ms": endpoint.avg_latency_ms,
            "uptime_percent": 99.9,
        })


# =============================================================================
# InferenceRequest
# =============================================================================


class InferenceRequestViewSet(viewsets.ModelViewSet):
    """
    Gestion de solicitudes de inferencia.

    - list:     solicitudes de la empresa del usuario.
    - create:   enviar una solicitud de inferencia.
    - retrieve: detalle de una solicitud.
    """

    serializer_class = InferenceRequestSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter requests by requester."""
        user = self.request.user
        if user.company:
            queryset = InferenceRequest.objects.filter(
                requester=user.company
            ).select_related("endpoint", "requester")

            endpoint_id = self.request.query_params.get("endpoint_id")
            if endpoint_id:
                queryset = queryset.filter(endpoint_id=endpoint_id)

            status_filter = self.request.query_params.get("status")
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            return queryset.order_by("-created_at")
        return InferenceRequest.objects.none()

    @action(detail=True, methods=["get"])
    def result(self, request, pk=None) -> Response:
        """Obtener resultado de una solicitud."""
        inference_request = self.get_object()

        if inference_request.status != InferenceRequest.Status.COMPLETED:
            return Response(
                {"detail": f"Request is {inference_request.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = inference_request.result
            return Response(InferenceResultSerializer(result).data)
        except InferenceResult.DoesNotExist:
            return Response(
                {"detail": "Result not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


# =============================================================================
# EdgeNode
# =============================================================================


class EdgeNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para nodos edge.
    """

    serializer_class = EdgeNodeSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "node_type"]
    search_fields = ["name", "location"]
    ordering_fields = ["created_at", "name", "status", "last_heartbeat"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter nodes by company."""
        user = self.request.user
        if user.company:
            return EdgeNode.objects.filter(company=user.company)
        return EdgeNode.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return EdgeNodeCreateSerializer
        return EdgeNodeSerializer

    @action(detail=True, methods=["post"])
    def heartbeat(self, request, pk=None) -> Response:
        """Actualizar heartbeat del nodo."""
        node = self.get_object()
        node.last_heartbeat = timezone.now()
        node.status = EdgeNode.Status.ONLINE
        node.save(update_fields=["last_heartbeat", "status"])

        return Response({
            "detail": "Heartbeat recorded.",
            "status": node.status,
            "last_heartbeat": node.last_heartbeat,
        })

    @action(detail=True, methods=["post"])
    def deploy_model(self, request, pk=None) -> Response:
        """Desplegar un modelo federado en este nodo."""
        node = self.get_object()

        serializer = DeployModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        model_id = serializer.validated_data["model_id"]

        try:
            model = FederatedModel.objects.get(id=model_id)
        except FederatedModel.DoesNotExist:
            return Response(
                {"detail": "Model not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if model.status not in [FederatedModel.Status.READY, FederatedModel.Status.DEPLOYED]:
            return Response(
                {"detail": "Model is not ready for deployment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        node.deployed_models.add(model)

        return Response({
            "detail": "Model deployed to node.",
            "node_id": str(node.id),
            "model_id": str(model.id),
        })

    @action(detail=True, methods=["post"])
    def undeploy_model(self, request, pk=None) -> Response:
        """Remover un modelo de este nodo."""
        node = self.get_object()

        serializer = DeployModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        model_id = serializer.validated_data["model_id"]

        try:
            model = FederatedModel.objects.get(id=model_id)
        except FederatedModel.DoesNotExist:
            return Response(
                {"detail": "Model not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        node.deployed_models.remove(model)

        return Response({
            "detail": "Model removed from node.",
            "node_id": str(node.id),
            "model_id": str(model.id),
        })

    @action(detail=False, methods=["get"])
    def online(self, request) -> Response:
        """Listar nodos online de la empresa."""
        user = request.user
        if not user.company:
            return Response([])

        nodes = EdgeNode.objects.filter(
            company=user.company,
            status=EdgeNode.Status.ONLINE,
        )

        serializer = EdgeNodeSerializer(nodes, many=True)
        return Response(serializer.data)
