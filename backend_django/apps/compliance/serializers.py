"""
Compliance serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import (
    Attestation,
    ComplianceCheck,
    ComplianceFramework,
    ComplianceReport,
    ConsortiumCompliance,
    DataProcessingRecord,
)


class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceFramework."""

    controls_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ComplianceFramework
        fields = [
            "id",
            "name",
            "version",
            "description",
            "region",
            "industry",
            "controls",
            "controls_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ConsortiumComplianceSerializer(serializers.ModelSerializer):
    """Serializer for ConsortiumCompliance."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    enabled_framework_ids = serializers.PrimaryKeyRelatedField(
        queryset=ComplianceFramework.objects.all(),
        many=True,
        source="enabled_frameworks",
        write_only=True,
    )
    enabled_frameworks = ComplianceFrameworkSerializer(many=True, read_only=True)
    next_check_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ConsortiumCompliance
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "enabled_frameworks",
            "enabled_framework_ids",
            "auto_check_interval",
            "notification_emails",
            "last_check_at",
            "next_check_at",
        ]
        read_only_fields = ["id", "last_check_at"]


class ComplianceCheckSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceCheck."""

    framework_name = serializers.CharField(source="framework.name", read_only=True)
    checked_by_name = serializers.CharField(source="checked_by.name", read_only=True)

    class Meta:
        model = ComplianceCheck
        fields = [
            "id",
            "consortium",
            "framework",
            "framework_name",
            "control_id",
            "status",
            "result",
            "evidence",
            "notes",
            "checked_by",
            "checked_by_name",
            "checked_at",
        ]
        read_only_fields = ["id", "checked_by", "checked_at"]


class ComplianceCheckCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ComplianceCheck."""

    class Meta:
        model = ComplianceCheck
        fields = [
            "consortium",
            "framework",
            "control_id",
            "status",
            "result",
            "evidence",
            "notes",
        ]

    def create(self, validated_data):
        """Create check with checked_by."""
        checked_by = self.context["request"].user.company
        return ComplianceCheck.objects.create(checked_by=checked_by, **validated_data)


class ComplianceReportSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceReport."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    framework_name = serializers.CharField(source="framework.name", read_only=True)

    class Meta:
        model = ComplianceReport
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "framework",
            "framework_name",
            "overall_score",
            "status",
            "passed_controls",
            "failed_controls",
            "pending_controls",
            "total_controls",
            "generated_at",
            "valid_until",
        ]
        read_only_fields = fields


class AttestationSerializer(serializers.ModelSerializer):
    """Serializer for Attestation."""

    attester_name = serializers.CharField(source="attester.name", read_only=True)
    framework_name = serializers.CharField(source="framework.name", read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Attestation
        fields = [
            "id",
            "consortium",
            "framework",
            "framework_name",
            "control_id",
            "attester",
            "attester_name",
            "attester_role",
            "attestation_type",
            "statement",
            "evidence_urls",
            "valid_from",
            "valid_until",
            "revoked",
            "revoked_at",
            "is_valid",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "attester",
            "revoked",
            "revoked_at",
            "created_at",
        ]


class AttestationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Attestation."""

    class Meta:
        model = Attestation
        fields = [
            "consortium",
            "framework",
            "control_id",
            "attester_role",
            "attestation_type",
            "statement",
            "evidence_urls",
            "valid_from",
            "valid_until",
        ]

    def create(self, validated_data):
        """Create attestation with attester."""
        attester = self.context["request"].user.company
        return Attestation.objects.create(attester=attester, **validated_data)


class DataProcessingRecordSerializer(serializers.ModelSerializer):
    """Serializer for DataProcessingRecord."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = DataProcessingRecord
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "company",
            "company_name",
            "processing_purpose",
            "data_categories",
            "legal_basis",
            "data_subjects",
            "recipients",
            "retention_period",
            "security_measures",
            "cross_border_transfer",
            "transfer_safeguards",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "company", "created_at", "updated_at"]


class DataProcessingRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating DataProcessingRecord."""

    class Meta:
        model = DataProcessingRecord
        fields = [
            "consortium",
            "processing_purpose",
            "data_categories",
            "legal_basis",
            "data_subjects",
            "recipients",
            "retention_period",
            "security_measures",
            "cross_border_transfer",
            "transfer_safeguards",
        ]

    def create(self, validated_data):
        """Create record with company."""
        company = self.context["request"].user.company
        return DataProcessingRecord.objects.create(company=company, **validated_data)


class GenerateReportSerializer(serializers.Serializer):
    """Serializer for generating compliance report."""

    consortium_id = serializers.UUIDField()
    framework_id = serializers.CharField()


class ComplianceSummarySerializer(serializers.Serializer):
    """Serializer for compliance summary."""

    framework_id = serializers.CharField()
    framework_name = serializers.CharField()
    overall_score = serializers.FloatField()
    status = serializers.CharField()
    passed = serializers.IntegerField()
    failed = serializers.IntegerField()
    pending = serializers.IntegerField()
