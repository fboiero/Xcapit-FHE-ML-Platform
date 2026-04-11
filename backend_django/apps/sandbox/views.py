"""
Sandbox views for Xcapit FHE-ML Platform.

Provides endpoints for sandbox environments, synthetic data, experiments,
trial management, and consortium demo.
"""

import random
from datetime import timedelta

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember, IsTrialActive
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DataUpload, Experiment, Sandbox, SandboxLead, SandboxTemplate, SyntheticDataset
from .services import ConsortiumDemoService, TrialService
from .serializers import (
    DataUploadSerializer,
    ExperimentCreateSerializer,
    ExperimentSerializer,
    GenerateDataSerializer,
    PlanComparisonSerializer,
    SandboxCreateSerializer,
    SandboxLeadRequestSerializer,
    SandboxLeadResponseSerializer,
    SandboxLeadVerifySerializer,
    SandboxSerializer,
    SandboxTemplateSerializer,
    SubscriptionSerializer,
    SyntheticDatasetCreateSerializer,
    SyntheticDatasetSerializer,
    TrialDataUploadSerializer,
    TrialStartSerializer,
    TrialUpgradeSerializer,
    TrialUsageSerializer,
)


# =============================================================================
# PUBLIC SANDBOX ACCESS (Lead Capture)
# =============================================================================


class SandboxLeadView(APIView):
    """
    Public endpoint for sandbox access via email.

    POST /api/v2/sandbox/leads/
    - Captures email for marketing
    - Returns sandbox access token (7 days validity)

    No authentication required.
    """

    permission_classes = [AllowAny]
    throttle_scope = "sandbox_lead"

    def post(self, request):
        """Request sandbox access with email."""
        serializer = SandboxLeadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Get or create lead
        lead, created = SandboxLead.get_or_create_for_email(
            email=email,
            source=serializer.validated_data.get("source", "direct"),
            utm_campaign=serializer.validated_data.get("utm_campaign", ""),
            utm_source=serializer.validated_data.get("utm_source", ""),
            utm_medium=serializer.validated_data.get("utm_medium", ""),
        )

        # Record access
        lead.record_access()

        return Response(
            SandboxLeadResponseSerializer(lead).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class SandboxLeadVerifyView(APIView):
    """
    Verify sandbox token validity.

    POST /api/v2/sandbox/leads/verify/
    - Checks if token is valid and not expired
    - Records access for analytics

    No authentication required.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Verify sandbox token."""
        serializer = SandboxLeadVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        try:
            lead = SandboxLead.objects.get(token=token)
        except SandboxLead.DoesNotExist:
            return Response(
                {"valid": False, "error": "Invalid token"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if lead.is_expired:
            return Response(
                {"valid": False, "error": "Token expired", "expired_at": lead.expires_at},
                status=status.HTTP_410_GONE,
            )

        # Record access
        lead.record_access()

        return Response({
            "valid": True,
            "email": lead.email,
            "expires_at": lead.expires_at,
        })


# =============================================================================
# SANDBOX TEMPLATES (Authenticated)
# =============================================================================


class SandboxTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for sandbox templates (read-only).
    """

    queryset = SandboxTemplate.objects.all()
    serializer_class = SandboxTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by industry if specified."""
        queryset = SandboxTemplate.objects.all()

        industry = self.request.query_params.get("industry")
        if industry:
            queryset = queryset.filter(industry=industry)

        return queryset


class SandboxViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sandbox environments.
    """

    serializer_class = SandboxSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter sandboxes by owner."""
        user = self.request.user
        if user.company:
            return Sandbox.objects.filter(owner=user.company)
        return Sandbox.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return SandboxCreateSerializer
        return SandboxSerializer

    def perform_create(self, serializer):
        """Create sandbox and log event."""
        sandbox = serializer.save()
        AuditLog.log(
            self.request,
            action="sandbox_created",
            resource_type="sandbox",
            resource_id=sandbox.id,
            extra_data={
                "name": sandbox.name,
                "industry": sandbox.industry,
            },
        )

    @action(detail=True, methods=["post"])
    def extend(self, request, pk=None):
        """Extend sandbox expiration."""
        sandbox = self.get_object()

        try:
            days = int(request.data.get("days", 7))
        except (TypeError, ValueError):
            return Response(
                {"detail": "days must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if days < 1 or days > 30:
            return Response(
                {"detail": "Extension must be between 1 and 30 days."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sandbox.expires_at = sandbox.expires_at + timedelta(days=days)
        sandbox.save(update_fields=["expires_at"])

        return Response({
            "detail": f"Sandbox extended by {days} days.",
            "new_expires_at": sandbox.expires_at,
        })

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive a sandbox."""
        sandbox = self.get_object()

        if sandbox.status == Sandbox.Status.ARCHIVED:
            return Response(
                {"detail": "Sandbox is already archived."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sandbox.status = Sandbox.Status.ARCHIVED
        sandbox.save(update_fields=["status"])

        return Response({"detail": "Sandbox archived."})

    @action(detail=True, methods=["get"])
    def datasets(self, request, pk=None):
        """Get datasets in this sandbox."""
        sandbox = self.get_object()
        datasets = SyntheticDataset.objects.filter(sandbox=sandbox)
        serializer = SyntheticDatasetSerializer(datasets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def experiments(self, request, pk=None):
        """Get experiments in this sandbox."""
        sandbox = self.get_object()
        experiments = Experiment.objects.filter(sandbox=sandbox)
        serializer = ExperimentSerializer(experiments, many=True)
        return Response(serializer.data)


class SyntheticDatasetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for synthetic datasets.
    """

    serializer_class = SyntheticDatasetSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter datasets by owner."""
        user = self.request.user
        if user.company:
            return SyntheticDataset.objects.filter(sandbox__owner=user.company)
        return SyntheticDataset.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return SyntheticDatasetCreateSerializer
        return SyntheticDatasetSerializer

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate synthetic data for a sandbox."""
        serializer = GenerateDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        sandbox_id = request.data.get("sandbox_id")
        if not sandbox_id:
            return Response(
                {"detail": "sandbox_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sandbox = Sandbox.objects.get(
                id=sandbox_id,
                owner=request.user.company,
            )
        except Sandbox.DoesNotExist:
            return Response(
                {"detail": "Sandbox not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if sandbox.is_expired or sandbox.status != Sandbox.Status.ACTIVE:
            return Response(
                {"detail": "Sandbox is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate synthetic data
        dataset_type = params["dataset_type"]
        record_count = params["record_count"]
        features = params.get("features", [])

        # Default features by type
        if not features:
            features = self._get_default_features(dataset_type)

        # Generate preview data (first 10 rows)
        preview = self._generate_preview(features, min(10, record_count))

        # Calculate statistics
        statistics = self._calculate_statistics(features, record_count)

        # Create dataset
        dataset = SyntheticDataset.objects.create(
            sandbox=sandbox,
            name=f"Synthetic {dataset_type} Dataset",
            dataset_type=dataset_type,
            industry=params.get("industry", ""),
            record_count=record_count,
            feature_count=len(features),
            features=features,
            statistics=statistics,
            data_preview=preview,
        )

        return Response(
            SyntheticDatasetSerializer(dataset).data,
            status=status.HTTP_201_CREATED,
        )

    def _get_default_features(self, dataset_type):
        """Get default features for a dataset type."""
        if dataset_type == SyntheticDataset.DatasetType.TRANSACTIONS:
            return [
                {"name": "amount", "type": "float", "min": 0, "max": 10000},
                {"name": "merchant_category", "type": "category", "values": ["retail", "food", "travel", "online"]},
                {"name": "hour", "type": "int", "min": 0, "max": 23},
                {"name": "is_fraud", "type": "bool", "true_ratio": 0.02},
            ]
        elif dataset_type == SyntheticDataset.DatasetType.PATIENTS:
            return [
                {"name": "age", "type": "int", "min": 18, "max": 90},
                {"name": "blood_pressure", "type": "float", "min": 80, "max": 180},
                {"name": "cholesterol", "type": "float", "min": 100, "max": 300},
                {"name": "diagnosis", "type": "category", "values": ["healthy", "at_risk", "condition"]},
            ]
        else:
            return [
                {"name": "feature_1", "type": "float", "min": 0, "max": 100},
                {"name": "feature_2", "type": "float", "min": 0, "max": 100},
                {"name": "label", "type": "bool", "true_ratio": 0.5},
            ]

    def _generate_preview(self, features, count):
        """Generate preview data rows."""
        rows = []
        for _ in range(count):
            row = {}
            for feature in features:
                name = feature["name"]
                ftype = feature["type"]

                if ftype == "float":
                    row[name] = round(random.uniform(feature.get("min", 0), feature.get("max", 100)), 2)
                elif ftype == "int":
                    row[name] = random.randint(feature.get("min", 0), feature.get("max", 100))
                elif ftype == "category":
                    row[name] = random.choice(feature.get("values", ["A", "B", "C"]))
                elif ftype == "bool":
                    row[name] = random.random() < feature.get("true_ratio", 0.5)
                else:
                    row[name] = None

            rows.append(row)
        return rows

    def _calculate_statistics(self, features, record_count):
        """Calculate synthetic statistics."""
        stats = {"record_count": record_count, "features": {}}

        for feature in features:
            name = feature["name"]
            ftype = feature["type"]

            if ftype in ["float", "int"]:
                min_val = feature.get("min", 0)
                max_val = feature.get("max", 100)
                stats["features"][name] = {
                    "type": ftype,
                    "min": min_val,
                    "max": max_val,
                    "mean": (min_val + max_val) / 2,
                }
            elif ftype == "category":
                values = feature.get("values", [])
                stats["features"][name] = {
                    "type": ftype,
                    "unique_values": len(values),
                    "values": values,
                }
            elif ftype == "bool":
                ratio = feature.get("true_ratio", 0.5)
                stats["features"][name] = {
                    "type": ftype,
                    "true_ratio": ratio,
                    "false_ratio": 1 - ratio,
                }

        return stats


class ExperimentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for experiments.
    """

    serializer_class = ExperimentSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter experiments by owner."""
        user = self.request.user
        if user.company:
            queryset = Experiment.objects.filter(sandbox__owner=user.company)

            # Filter by sandbox
            sandbox_id = self.request.query_params.get("sandbox_id")
            if sandbox_id:
                queryset = queryset.filter(sandbox_id=sandbox_id)

            # Filter by status
            status_filter = self.request.query_params.get("status")
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            return queryset
        return Experiment.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ExperimentCreateSerializer
        return ExperimentSerializer

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """Run an experiment."""
        experiment = self.get_object()

        if experiment.status not in [Experiment.Status.PENDING, Experiment.Status.FAILED]:
            return Response(
                {"detail": f"Experiment is already {experiment.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Start experiment
        experiment.start()

        # Simulate experiment (in real implementation, this would be async)
        try:
            results = self._run_experiment(experiment)
            experiment.complete(results)
            message = "Experiment completed."
        except Exception as e:
            experiment.fail(str(e))
            message = f"Experiment failed: {str(e)}"

        return Response({
            "detail": message,
            "status": experiment.status,
            "results": experiment.results,
        })

    def _run_experiment(self, experiment):
        """Run the experiment and return results."""
        # This is a simplified simulation
        # In production, this would call actual ML/FHE operations

        exp_type = experiment.experiment_type
        config = experiment.config

        if exp_type == Experiment.ExperimentType.TRAINING:
            return {
                "accuracy": round(random.uniform(0.75, 0.95), 4),
                "loss": round(random.uniform(0.05, 0.25), 4),
                "epochs_completed": config.get("epochs", 10),
                "training_time_seconds": random.randint(10, 120),
            }
        elif exp_type == Experiment.ExperimentType.EVALUATION:
            return {
                "accuracy": round(random.uniform(0.70, 0.90), 4),
                "precision": round(random.uniform(0.70, 0.90), 4),
                "recall": round(random.uniform(0.70, 0.90), 4),
                "f1_score": round(random.uniform(0.70, 0.90), 4),
            }
        elif exp_type == Experiment.ExperimentType.CLUSTERING:
            n_clusters = config.get("n_clusters", 3)
            return {
                "n_clusters": n_clusters,
                "inertia": round(random.uniform(100, 1000), 2),
                "silhouette_score": round(random.uniform(0.3, 0.8), 4),
            }
        elif exp_type == Experiment.ExperimentType.ENCRYPTION_BENCHMARK:
            return {
                "encryption_time_ms": round(random.uniform(10, 100), 2),
                "decryption_time_ms": round(random.uniform(5, 50), 2),
                "computation_time_ms": round(random.uniform(50, 500), 2),
                "ciphertext_size_kb": random.randint(100, 1000),
            }
        else:
            return {"status": "completed"}

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a running experiment."""
        experiment = self.get_object()

        if experiment.status != Experiment.Status.RUNNING:
            return Response(
                {"detail": "Experiment is not running."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        experiment.fail("Cancelled by user")

        return Response({"detail": "Experiment cancelled."})


# =============================================================================
# CONSORTIUM DEMO (Public with sandbox token)
# =============================================================================


class ConsortiumDemoView(APIView):
    """
    Run a consortium demo with FHE.

    POST /api/v2/sandbox/consortium-demo/
    Accepts sandbox token or authenticated user.
    """

    permission_classes = [AllowAny]
    throttle_scope = "sandbox_demo"

    def post(self, request):
        members = request.data.get("members", [])
        if not members or not isinstance(members, list):
            return Response(
                {"detail": "Se requiere una lista de 'members'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tier = "free"
        # If authenticated, use company tier
        if request.user and request.user.is_authenticated:
            company = getattr(request.user, "company", None)
            if company:
                tier = company.tier

        service = ConsortiumDemoService()
        result = service.run_demo(members=members, tier=tier)

        if not result.success:
            return Response(
                {"detail": result.error, "error_code": result.error_code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result.data)


class ConsortiumDemoLimitsView(APIView):
    """
    GET /api/v2/sandbox/consortium-demo/limits/
    Returns tier limits for the consortium demo.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        tier = "free"
        if request.user and request.user.is_authenticated:
            company = getattr(request.user, "company", None)
            if company:
                tier = company.tier

        limits = ConsortiumDemoService.get_tier_limits(tier)
        return Response({"tier": tier, "limits": limits})


# =============================================================================
# TRIAL MANAGEMENT
# =============================================================================


class TrialStartView(APIView):
    """
    POST /api/v2/sandbox/trial/start/
    Start a 14-day trial for the authenticated company.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        service = TrialService()
        result = service.start_trial(request.user.company)

        if not result.success:
            return Response(
                {"detail": result.error, "error_code": result.error_code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        AuditLog.log(
            request,
            action="trial_started",
            resource_type="company",
            resource_id=request.user.company.id,
        )

        return Response(result.data, status=status.HTTP_201_CREATED)


class TrialStatusView(APIView):
    """
    GET /api/v2/sandbox/trial/status/
    Returns current trial/subscription status.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.user.company
        service = TrialService()
        result = service.get_usage_summary(company)

        if not result.success:
            return Response(
                {"detail": result.error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Include subscription info if available
        data = result.data
        sub = getattr(company, "subscription", None)
        if sub:
            data["subscription"] = SubscriptionSerializer(sub).data

        return Response(data)


class TrialUsageView(APIView):
    """
    GET /api/v2/sandbox/trial/usage/
    Detailed usage breakdown.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        service = TrialService()
        result = service.get_usage_summary(request.user.company)

        if not result.success:
            return Response(
                {"detail": result.error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result.data)


class TrialUpgradeView(APIView):
    """
    POST /api/v2/sandbox/trial/upgrade/
    Request an upgrade to a paid tier.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        serializer = TrialUpgradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = TrialService()
        result = service.request_upgrade(
            request.user.company,
            serializer.validated_data["target_tier"],
        )

        if not result.success:
            return Response(
                {"detail": result.error, "error_code": result.error_code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        AuditLog.log(
            request,
            action="tier_upgrade_requested",
            resource_type="company",
            resource_id=request.user.company.id,
            extra_data={
                "current_tier": result.data.get("current_tier", result.data.get("old_tier")),
                "requested_tier": result.data.get("requested_tier", result.data.get("new_tier")),
            },
        )

        return Response(result.data)


class TrialUploadDataView(APIView):
    """
    POST /api/v2/sandbox/trial/upload-data/
    Upload data to a consortium (with trial limit enforcement).
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsTrialActive]
    parser_classes = [MultiPartParser]

    def post(self, request):
        from apps.consortiums.models import Consortium

        consortium_id = request.data.get("consortium_id")
        uploaded_file = request.FILES.get("file")

        if not consortium_id or not uploaded_file:
            return Response(
                {"detail": "Se requiere 'consortium_id' y 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate consortium access
        try:
            consortium = Consortium.objects.get(id=consortium_id)
        except Consortium.DoesNotExist:
            return Response(
                {"detail": "Consorcio no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        company = request.user.company

        # SECURITY: Verify user's company is owner or active member
        from apps.consortiums.models import ConsortiumMember

        is_owner = consortium.owner_id == company.id
        is_member = ConsortiumMember.objects.filter(
            consortium=consortium,
            company=company,
            status="active",
        ).exists()
        if not is_owner and not is_member:
            return Response(
                {"detail": "No tienes acceso a este consorcio."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check upload limits
        service = TrialService()
        check = service.check_upload_allowed(company, uploaded_file.size)
        if not check.success:
            return Response(
                {"detail": check.error, "error_code": check.error_code},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse the file to extract record/feature counts
        import csv
        import hashlib
        import io

        record_count = 0
        feature_count = 0
        data_hash = ""
        preview_rows = []
        error_msg = ""

        try:
            content = uploaded_file.read()
            data_hash = hashlib.sha256(content).hexdigest()

            if uploaded_file.name.endswith(".csv"):
                text = content.decode("utf-8")
                reader = csv.DictReader(io.StringIO(text))
                rows = list(reader)
                record_count = len(rows)
                feature_count = len(reader.fieldnames) if reader.fieldnames else 0
                preview_rows = rows[:5]
            elif uploaded_file.name.endswith(".json"):
                import json

                data = json.loads(content)
                if isinstance(data, list):
                    record_count = len(data)
                    feature_count = len(data[0].keys()) if data else 0
                    preview_rows = data[:5]
                else:
                    record_count = 1
                    feature_count = len(data.keys())
                    preview_rows = [data]
            else:
                record_count = uploaded_file.size // 100  # Estimate
                feature_count = 0

            upload_status = "completed"
        except Exception as e:
            error_msg = str(e)
            upload_status = "failed"

        # Record the upload
        upload = DataUpload.objects.create(
            company=company,
            consortium=consortium,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            record_count=record_count,
            feature_count=feature_count,
            status=upload_status,
            error_message=error_msg,
        )

        # Create ContributionProof if successful
        if upload_status == "completed":
            from apps.consortiums.models import ContributionProof

            ContributionProof.objects.create(
                consortium=consortium,
                company=company,
                record_count=record_count,
                feature_count=feature_count,
                data_hash=data_hash,
                checksum=data_hash[:16],
                verification_status="verified",
                verification_message="Datos validados automaticamente.",
            )

        AuditLog.log(
            request,
            action="data_uploaded",
            resource_type="data_upload",
            resource_id=upload.id,
            extra_data={
                "file_name": uploaded_file.name,
                "file_size": uploaded_file.size,
                "record_count": record_count,
                "feature_count": feature_count,
                "consortium_id": str(consortium_id),
                "data_hash": data_hash[:16],
            },
        )

        response_data = DataUploadSerializer(upload).data
        response_data["preview"] = preview_rows
        response_data["data_hash"] = data_hash[:16]

        return Response(response_data, status=status.HTTP_201_CREATED)


class PlansComparisonView(APIView):
    """
    GET /api/v2/sandbox/plans/
    Public endpoint showing plan comparison.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        plans = TrialService.get_plans_comparison()
        return Response(plans)
