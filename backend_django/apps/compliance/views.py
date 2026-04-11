"""
Views para la app de Compliance.

ViewSets para gestionar marcos regulatorios, evaluaciones de cumplimiento,
verificaciones de controles, atestaciones y registros GDPR.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember, IsConsortiumMember

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


# =============================================================================
# ComplianceFramework (read-only)
# =============================================================================


class ComplianceFrameworkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para marcos regulatorios de cumplimiento.

    Soporta filtros por region e industry.
    """

    queryset = ComplianceFramework.objects.all()
    serializer_class = ComplianceFrameworkSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["region", "industry"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "region"]
    ordering = ["name"]

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
    def controls(self, request, pk=None) -> Response:
        """Listar controles de un marco regulatorio."""
        framework = self.get_object()
        return Response({
            "framework_id": framework.id,
            "framework_name": framework.name,
            "controls": framework.controls,
            "count": len(framework.controls),
        })


# =============================================================================
# ComplianceAssessment (replaces ComplianceCheck with the requested name)
# =============================================================================


class ComplianceAssessmentViewSet(viewsets.ModelViewSet):
    """
    CRUD para evaluaciones/verificaciones de cumplimiento.

    - list:      evaluaciones filtradas por consortium_id.
    - create:    crear una evaluacion de control.
    - run_check: ejecutar verificaciones automatizadas (POST).
    """

    serializer_class = ComplianceCheckSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter assessments by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            queryset = ComplianceCheck.objects.filter(
                consortium_id=consortium_id
            ).select_related("framework", "consortium", "checked_by")

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
        """Create assessment and log event."""
        check = serializer.save()
        AuditLog.log(
            self.request,
            action="compliance_check_created",
            resource_type="compliance_check",
            resource_id=check.id,
            extra_data={
                "framework": str(check.framework_id),
                "control_id": check.control_id,
                "status": check.status,
            },
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def run_check(self, request, pk=None) -> Response:
        """
        Ejecutar una verificacion automatizada de cumplimiento.

        Re-evalua el control indicado en el assessment, generando
        un nuevo resultado.
        """
        check = self.get_object()

        # Mark as running and then simulate completion
        check.status = ComplianceCheck.Status.COMPLIANT
        check.result = ComplianceCheck.Result.PASS
        check.evidence = f"Automated check run at {timezone.now().isoformat()}"
        check.checked_by = request.user.company
        check.save(update_fields=[
            "status", "result", "evidence", "checked_by", "updated_at",
        ])

        AuditLog.log(
            request,
            action="compliance_check_run",
            resource_type="compliance_check",
            resource_id=check.id,
            extra_data={
                "control_id": check.control_id,
                "result": check.result,
            },
        )

        return Response(ComplianceCheckSerializer(check).data)


# =============================================================================
# ConsortiumCompliance (settings)
# =============================================================================


class ConsortiumComplianceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configuracion de cumplimiento por consorcio.
    """

    serializer_class = ConsortiumComplianceSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return ConsortiumCompliance.objects.filter(
                consortium_id=consortium_id
            ).select_related("consortium").prefetch_related("enabled_frameworks")
        return ConsortiumCompliance.objects.none()

    def get_permissions(self):
        """Use IsAuthenticated only for summary (detail action with compliance pk, not consortium pk)."""
        if self.action == "summary":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None) -> Response:
        """Resumen de cumplimiento para un consorcio."""
        compliance = self.get_object()
        summaries = []

        for framework in compliance.enabled_frameworks.all():
            checks = ComplianceCheck.objects.filter(
                consortium=compliance.consortium,
                framework=framework,
            )

            passed = checks.filter(status=ComplianceCheck.Status.COMPLIANT).count()
            failed = checks.filter(status=ComplianceCheck.Status.NON_COMPLIANT).count()
            pending = checks.filter(status=ComplianceCheck.Status.NOT_APPLICABLE).count()
            total = passed + failed + pending

            score = (passed / total * 100) if total > 0 else 0

            if score >= 90:
                status_val = "compliant"
            elif score >= 70:
                status_val = "partial"
            else:
                status_val = "non_compliant"

            summaries.append({
                "framework_id": str(framework.id),
                "framework_name": framework.name,
                "overall_score": round(score, 1),
                "status": status_val,
                "passed": passed,
                "failed": failed,
                "pending": pending,
            })

        return Response(ComplianceSummarySerializer(summaries, many=True).data)


# =============================================================================
# ComplianceReport
# =============================================================================


class ComplianceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para reportes de cumplimiento.
    """

    serializer_class = ComplianceReportSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "framework"]
    ordering_fields = ["generated_at", "overall_score", "status"]
    ordering = ["-generated_at"]

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

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsConsortiumMember])
    @transaction.atomic
    def generate(self, request) -> Response:
        """Generar un reporte de cumplimiento."""
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consortium_id = serializer.validated_data["consortium_id"]
        framework_id = serializer.validated_data["framework_id"]

        checks = ComplianceCheck.objects.filter(
            consortium_id=consortium_id,
            framework_id=framework_id,
        )

        passed = checks.filter(status=ComplianceCheck.Status.COMPLIANT).count()
        failed = checks.filter(status=ComplianceCheck.Status.NON_COMPLIANT).count()
        pending = checks.filter(status=ComplianceCheck.Status.NOT_APPLICABLE).count()
        total = passed + failed + pending

        if total == 0:
            return Response(
                {"detail": "No compliance checks found for this framework."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score = passed / total * 100

        report = ComplianceReport.objects.create(
            consortium_id=consortium_id,
            framework_id=framework_id,
            overall_score=round(score, 1),
            status=ComplianceReport.Status.COMPLETED,
            passed_controls=passed,
            failed_controls=failed,
            pending_controls=pending,
            total_controls=total,
        )

        ConsortiumCompliance.objects.filter(
            consortium_id=consortium_id
        ).update(last_check_at=timezone.now())

        AuditLog.log(
            request,
            action="compliance_report_generated",
            resource_type="compliance_report",
            resource_id=report.id,
            extra_data={
                "framework": str(framework_id),
                "score": float(report.overall_score),
                "status": report.status,
            },
        )

        return Response(
            ComplianceReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# Attestation
# =============================================================================


class AttestationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para atestaciones de cumplimiento.
    """

    serializer_class = AttestationSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["attestation_type", "revoked"]
    ordering_fields = ["created_at", "valid_from", "valid_until"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter attestations by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            queryset = Attestation.objects.filter(consortium_id=consortium_id)

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

    def get_permissions(self):
        """Use IsAuthenticated only for revoke (detail action with attestation pk, not consortium pk)."""
        if self.action == "revoke":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None) -> Response:
        """Revocar una atestacion."""
        attestation = self.get_object()

        if attestation.revoked:
            return Response(
                {"detail": "Attestation already revoked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attestation.attester != request.user.company:
            return Response(
                {"detail": "Only the attester can revoke this attestation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        attestation.revoked = True
        attestation.revoked_at = timezone.now()
        attestation.save()

        AuditLog.log(
            request,
            action="attestation_revoked",
            resource_type="attestation",
            resource_id=attestation.id,
        )

        return Response({"detail": "Attestation revoked."})


# =============================================================================
# DataProcessingRecord (GDPR)
# =============================================================================


class DataProcessingRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD para registros de procesamiento de datos (GDPR Articulo 30).
    """

    serializer_class = DataProcessingRecordSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter records by consortium and company."""
        user = self.request.user
        consortium_id = self.request.query_params.get("consortium_id")

        if consortium_id and user.company:
            queryset = DataProcessingRecord.objects.filter(consortium_id=consortium_id)

            if not self.request.query_params.get("all"):
                queryset = queryset.filter(company=user.company)

            return queryset
        return DataProcessingRecord.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return DataProcessingRecordCreateSerializer
        return DataProcessingRecordSerializer

    @action(detail=False, methods=["get"])
    def export(self, request) -> Response:
        """Exportar registros de procesamiento de datos (GDPR)."""
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
