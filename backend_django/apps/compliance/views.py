"""
Compliance views for Xcapit FHE-ML Platform.

Provides endpoints for compliance frameworks, checks, reports, and attestations.
"""

from apps.core.models import AuditLog
from apps.core.permissions import IsConsortiumAdmin, IsConsortiumMember
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Attestation,
    ComplianceCheck,
    ComplianceFramework,
    ComplianceReport,
    ConsortiumCompliance,
    DataProcessingRecord,
)
from .serializers import (
    AttestationCreateSerializer,
    AttestationSerializer,
    ComplianceCheckCreateSerializer,
    ComplianceCheckSerializer,
    ComplianceFrameworkSerializer,
    ComplianceReportSerializer,
    ComplianceSummarySerializer,
    ConsortiumComplianceSerializer,
    DataProcessingRecordCreateSerializer,
    DataProcessingRecordSerializer,
    GenerateReportSerializer,
)


class ComplianceFrameworkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for compliance frameworks (read-only).
    """

    queryset = ComplianceFramework.objects.all()
    serializer_class = ComplianceFrameworkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by region/industry if specified."""
        queryset = ComplianceFramework.objects.all()

        region = self.request.query_params.get("region")
        if region:
            queryset = queryset.filter(region=region)

        industry = self.request.query_params.get("industry")
        if industry:
            queryset = queryset.filter(Q(industry=industry) | Q(industry=""))

        return queryset

    @action(detail=True, methods=["get"])
    def controls(self, request, pk=None):
        """Get controls for a framework."""
        framework = self.get_object()
        return Response({
            "framework_id": framework.id,
            "framework_name": framework.name,
            "controls": framework.controls,
            "count": len(framework.controls),
        })


class ConsortiumComplianceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for consortium compliance settings.
    """

    serializer_class = ConsortiumComplianceSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return ConsortiumCompliance.objects.filter(consortium_id=consortium_id)
        return ConsortiumCompliance.objects.none()

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Get compliance summary for a consortium."""
        compliance = self.get_object()
        summaries = []

        for framework in compliance.enabled_frameworks.all():
            # Get latest checks
            checks = ComplianceCheck.objects.filter(
                consortium=compliance.consortium,
                framework=framework,
            )

            passed = checks.filter(status=ComplianceCheck.Status.PASSED).count()
            failed = checks.filter(status=ComplianceCheck.Status.FAILED).count()
            pending = checks.filter(status=ComplianceCheck.Status.PENDING).count()
            total = passed + failed + pending

            score = (passed / total * 100) if total > 0 else 0

            if score >= 90:
                status_val = "compliant"
            elif score >= 70:
                status_val = "partial"
            else:
                status_val = "non_compliant"

            summaries.append({
                "framework_id": framework.id,
                "framework_name": framework.name,
                "overall_score": round(score, 1),
                "status": status_val,
                "passed": passed,
                "failed": failed,
                "pending": pending,
            })

        return Response(ComplianceSummarySerializer(summaries, many=True).data)


class ComplianceCheckViewSet(viewsets.ModelViewSet):
    """
    ViewSet for compliance checks.
    """

    serializer_class = ComplianceCheckSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter checks by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            queryset = ComplianceCheck.objects.filter(consortium_id=consortium_id)

            # Optional filters
            framework_id = self.request.query_params.get("framework_id")
            if framework_id:
                queryset = queryset.filter(framework_id=framework_id)

            status_filter = self.request.query_params.get("status")
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            return queryset
        return ComplianceCheck.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ComplianceCheckCreateSerializer
        return ComplianceCheckSerializer

    def perform_create(self, serializer):
        """Create check and log event."""
        check = serializer.save()
        AuditLog.log(
            self.request,
            action="compliance_check_created",
            resource_type="compliance_check",
            resource_id=check.id,
            extra_data={
                "framework": check.framework_id,
                "control_id": check.control_id,
                "status": check.status,
            },
        )


class ComplianceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for compliance reports (read-only, generated automatically).
    """

    serializer_class = ComplianceReportSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter reports by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            queryset = ComplianceReport.objects.filter(consortium_id=consortium_id)

            framework_id = self.request.query_params.get("framework_id")
            if framework_id:
                queryset = queryset.filter(framework_id=framework_id)

            return queryset
        return ComplianceReport.objects.none()

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsConsortiumAdmin])
    def generate(self, request):
        """Generate a compliance report."""
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consortium_id = serializer.validated_data["consortium_id"]
        framework_id = serializer.validated_data["framework_id"]

        # Get checks
        checks = ComplianceCheck.objects.filter(
            consortium_id=consortium_id,
            framework_id=framework_id,
        )

        passed = checks.filter(status=ComplianceCheck.Status.PASSED).count()
        failed = checks.filter(status=ComplianceCheck.Status.FAILED).count()
        pending = checks.filter(status=ComplianceCheck.Status.PENDING).count()
        total = passed + failed + pending

        if total == 0:
            return Response(
                {"detail": "No compliance checks found for this framework."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score = passed / total * 100

        if score >= 90:
            report_status = ComplianceReport.Status.COMPLIANT
        elif score >= 70:
            report_status = ComplianceReport.Status.PARTIAL
        else:
            report_status = ComplianceReport.Status.NON_COMPLIANT

        # Create report
        report = ComplianceReport.objects.create(
            consortium_id=consortium_id,
            framework_id=framework_id,
            overall_score=round(score, 1),
            status=report_status,
            passed_controls=passed,
            failed_controls=failed,
            pending_controls=pending,
            total_controls=total,
        )

        # Update last check time
        ConsortiumCompliance.objects.filter(
            consortium_id=consortium_id
        ).update(last_check_at=timezone.now())

        # Log event
        AuditLog.log(
            request,
            action="compliance_report_generated",
            resource_type="compliance_report",
            resource_id=report.id,
            extra_data={
                "framework": framework_id,
                "score": report.overall_score,
                "status": report.status,
            },
        )

        return Response(ComplianceReportSerializer(report).data, status=status.HTTP_201_CREATED)


class AttestationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for compliance attestations.
    """

    serializer_class = AttestationSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter attestations by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            queryset = Attestation.objects.filter(consortium_id=consortium_id)

            # Filter valid only
            valid_only = self.request.query_params.get("valid_only")
            if valid_only == "true":
                now = timezone.now()
                queryset = queryset.filter(
                    revoked=False,
                    valid_from__lte=now,
                ).filter(
                    Q(valid_until__isnull=True) | Q(valid_until__gte=now)
                )

            return queryset
        return Attestation.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return AttestationCreateSerializer
        return AttestationSerializer

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """Revoke an attestation."""
        attestation = self.get_object()

        if attestation.revoked:
            return Response(
                {"detail": "Attestation already revoked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only attester can revoke
        if attestation.attester != request.user.company:
            return Response(
                {"detail": "Only the attester can revoke this attestation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        attestation.revoked = True
        attestation.revoked_at = timezone.now()
        attestation.save()

        # Log event
        AuditLog.log(
            request,
            action="attestation_revoked",
            resource_type="attestation",
            resource_id=attestation.id,
        )

        return Response({"detail": "Attestation revoked."})


class DataProcessingRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for GDPR Article 30 data processing records.
    """

    serializer_class = DataProcessingRecordSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter records by consortium and company."""
        user = self.request.user
        consortium_id = self.request.query_params.get("consortium_id")

        if consortium_id and user.company:
            # Can see own company's records or all if admin
            queryset = DataProcessingRecord.objects.filter(consortium_id=consortium_id)

            # Non-admins only see their own records
            if not self.request.query_params.get("all"):
                queryset = queryset.filter(company=user.company)

            return queryset
        return DataProcessingRecord.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return DataProcessingRecordCreateSerializer
        return DataProcessingRecordSerializer

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Export all data processing records for a consortium (GDPR export)."""
        consortium_id = request.query_params.get("consortium_id")
        if not consortium_id:
            return Response(
                {"detail": "consortium_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = DataProcessingRecord.objects.filter(
            consortium_id=consortium_id,
            company=request.user.company,
        )

        serializer = DataProcessingRecordSerializer(records, many=True)

        return Response({
            "consortium_id": consortium_id,
            "company": request.user.company.name,
            "exported_at": timezone.now(),
            "record_count": records.count(),
            "records": serializer.data,
        })
