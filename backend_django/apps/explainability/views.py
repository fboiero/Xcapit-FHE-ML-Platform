"""
Explainability views for Xcapit FHE-ML Platform.
"""

import random

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember, IsConsortiumMember

from .models import ExplanationRequest, FeatureImportance, ModelInsight
from .serializers import (
    ExplanationRequestCreateSerializer,
    ExplanationRequestSerializer,
    FeatureImportanceSerializer,
    ModelInsightSerializer,
)


class ExplanationRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for explanation requests.
    """

    serializer_class = ExplanationRequestSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter requests by user's company."""
        user = self.request.user
        if not user.company:
            return ExplanationRequest.objects.none()

        queryset = ExplanationRequest.objects.filter(requester=user.company)

        # Filter by consortium if provided
        consortium_id = self.request.query_params.get("consortium")
        if consortium_id:
            queryset = queryset.filter(consortium_id=consortium_id)

        # Filter by status if provided
        request_status = self.request.query_params.get("status")
        if request_status:
            queryset = queryset.filter(status=request_status)

        return queryset.select_related("consortium", "requester")

    def get_serializer_class(self):
        if self.action == "create":
            return ExplanationRequestCreateSerializer
        return ExplanationRequestSerializer

    def perform_create(self, serializer):
        """Create request and log event."""
        request_obj = serializer.save()

        AuditLog.log(
            self.request,
            action="explanation_requested",
            resource_type="explanation_request",
            resource_id=request_obj.id,
            extra_data={"type": request_obj.explanation_type},
        )

        # Trigger async processing (for now, process synchronously)
        self._process_explanation(request_obj)

    def _process_explanation(self, request_obj):
        """Process explanation request."""
        request_obj.status = ExplanationRequest.Status.PROCESSING
        request_obj.save(update_fields=["status"])

        try:
            explanation = self._generate_explanation(request_obj)
            request_obj.mark_completed(explanation)
        except Exception as e:
            request_obj.mark_failed(str(e))

    def _generate_explanation(self, request_obj):
        """Generate explanation based on type."""
        if request_obj.explanation_type == ExplanationRequest.ExplanationType.FEATURE_IMPORTANCE:
            return self._generate_feature_importance(request_obj)
        elif request_obj.explanation_type == ExplanationRequest.ExplanationType.SHAP:
            return self._generate_shap_values(request_obj)
        elif request_obj.explanation_type == ExplanationRequest.ExplanationType.DECISION_PATH:
            return self._generate_decision_path(request_obj)
        elif request_obj.explanation_type == ExplanationRequest.ExplanationType.SUMMARY:
            return self._generate_summary(request_obj)
        else:
            return {"message": "Explanation type not implemented"}

    def _generate_feature_importance(self, request_obj):
        """Generate feature importance explanation."""
        # Get stored feature importances or generate simulated
        importances = FeatureImportance.objects.filter(
            consortium=request_obj.consortium
        ).order_by("importance_rank")[:10]

        if importances.exists():
            return {
                "features": [
                    {
                        "name": fi.feature_name,
                        "importance": fi.importance_score,
                        "rank": fi.importance_rank,
                    }
                    for fi in importances
                ]
            }

        # Generate simulated data
        features = ["income", "age", "credit_score", "employment_years", "debt_ratio"]
        return {
            "features": [
                {
                    "name": f,
                    "importance": round(random.uniform(0.1, 0.3), 4),
                    "rank": i + 1,
                }
                for i, f in enumerate(features)
            ]
        }

    def _generate_shap_values(self, request_obj):
        """Generate SHAP values explanation."""
        # Simulated SHAP values
        features = ["income", "age", "credit_score", "employment_years", "debt_ratio"]
        return {
            "base_value": 0.5,
            "shap_values": {
                f: round(random.uniform(-0.2, 0.2), 4)
                for f in features
            },
            "expected_value": round(random.uniform(0.4, 0.6), 4),
        }

    def _generate_decision_path(self, request_obj):
        """Generate decision path explanation."""
        return {
            "path": [
                {"node": 0, "feature": "income", "threshold": 50000, "direction": "left"},
                {"node": 1, "feature": "credit_score", "threshold": 700, "direction": "right"},
                {"node": 4, "feature": "age", "threshold": 30, "direction": "left"},
            ],
            "leaf_value": 0.75,
            "samples_at_leaf": 150,
        }

    def _generate_summary(self, request_obj):
        """Generate model summary."""
        return {
            "model_type": "logistic_regression",
            "n_features": 5,
            "n_samples_trained": 10000,
            "performance": {
                "accuracy": 0.85,
                "precision": 0.83,
                "recall": 0.87,
            },
            "top_features": ["income", "credit_score", "employment_years"],
        }


class FeatureImportanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for feature importance (read-only).
    """

    serializer_class = FeatureImportanceSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter by consortium."""
        consortium_id = self.kwargs.get("consortium_pk")
        return FeatureImportance.objects.filter(
            consortium_id=consortium_id
        ).order_by("importance_rank")

    @action(detail=False, methods=["get"])
    def top(self, request, consortium_pk=None):
        """Get top N features."""
        n = int(request.query_params.get("n", 10))
        features = self.get_queryset()[:n]
        return Response(FeatureImportanceSerializer(features, many=True).data)


class ModelInsightViewSet(viewsets.ModelViewSet):
    """
    ViewSet for model insights.
    """

    serializer_class = ModelInsightSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter by consortium."""
        consortium_id = self.kwargs.get("consortium_pk")
        queryset = ModelInsight.objects.filter(consortium_id=consortium_id)

        # Filter active only by default
        if self.request.query_params.get("include_inactive") != "true":
            queryset = queryset.filter(is_active=True)

        return queryset

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, consortium_pk=None, pk=None):
        """Acknowledge an insight."""
        insight = self.get_object()

        if insight.acknowledged:
            return Response(
                {"detail": "Insight already acknowledged."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        insight.acknowledge(request.user)

        AuditLog.log(
            request,
            action="insight_acknowledged",
            resource_type="model_insight",
            resource_id=insight.id,
        )

        return Response(ModelInsightSerializer(insight).data)

    @action(detail=False, methods=["get"])
    def summary(self, request, consortium_pk=None):
        """Get insights summary."""
        queryset = self.get_queryset()

        summary = {
            "total": queryset.count(),
            "by_type": dict(
                queryset.values("insight_type").annotate(count=Count("id")).values_list(
                    "insight_type", "count"
                )
            ),
            "by_severity": dict(
                queryset.values("severity").annotate(count=Count("id")).values_list(
                    "severity", "count"
                )
            ),
            "unacknowledged": queryset.filter(acknowledged=False).count(),
        }

        return Response(summary)


class ExplainabilityDashboardView(viewsets.ViewSet):
    """
    ViewSet for explainability dashboard.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def list(self, request):
        """Get explainability dashboard data."""
        user = request.user
        if not user.company:
            return Response({"detail": "No company associated."}, status=400)

        # Get explanation requests
        requests = ExplanationRequest.objects.filter(requester=user.company)

        # Get insights from consortiums user is member of
        from apps.consortiums.models import ConsortiumMember

        member_consortiums = ConsortiumMember.objects.filter(
            company=user.company,
            status=ConsortiumMember.Status.ACTIVE,
        ).values_list("consortium_id", flat=True)

        insights = ModelInsight.objects.filter(
            consortium_id__in=member_consortiums,
            is_active=True,
        )

        dashboard_data = {
            "total_requests": requests.count(),
            "pending_requests": requests.filter(
                status=ExplanationRequest.Status.PENDING
            ).count(),
            "active_insights": ModelInsightSerializer(
                insights.order_by("-created_at")[:5],
                many=True,
            ).data,
            "recent_explanations": ExplanationRequestSerializer(
                requests.filter(status=ExplanationRequest.Status.COMPLETED).order_by(
                    "-completed_at"
                )[:5],
                many=True,
            ).data,
        }

        return Response(dashboard_data)
