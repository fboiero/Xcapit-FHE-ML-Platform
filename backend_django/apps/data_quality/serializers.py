"""
Data quality serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from apps.consortiums.models import ConsortiumMember

from .models import QualityAlert, QualityAssessment, QualityRule


class QualityAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for QualityAssessment model."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    consortium_name = serializers.CharField(source="consortium.name", read_only=True)

    class Meta:
        model = QualityAssessment
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "company",
            "company_name",
            "contribution",
            "record_count",
            "feature_count",
            "null_count",
            "duplicate_count",
            "outlier_count",
            "schema_violations",
            "format_violations",
            "range_violations",
            "completeness_score",
            "consistency_score",
            "accuracy_score",
            "timeliness_score",
            "overall_score",
            "status",
            "created_at",
            "last_assessed_at",
        ]
        read_only_fields = [
            "id",
            "completeness_score",
            "consistency_score",
            "accuracy_score",
            "timeliness_score",
            "overall_score",
            "status",
            "created_at",
            "last_assessed_at",
        ]


class QualityAssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating QualityAssessment."""

    class Meta:
        model = QualityAssessment
        fields = [
            "id",
            "consortium",
            "contribution",
            "record_count",
            "feature_count",
            "null_count",
            "duplicate_count",
            "outlier_count",
            "schema_violations",
            "format_violations",
            "range_violations",
            "completeness_score",
            "consistency_score",
            "accuracy_score",
            "timeliness_score",
            "overall_score",
            "status",
        ]
        read_only_fields = [
            "id",
            "completeness_score",
            "consistency_score",
            "accuracy_score",
            "timeliness_score",
            "overall_score",
            "status",
        ]

    def validate_consortium(self, value):
        """SECURITY: Verify user is a member of the target consortium."""
        user = self.context["request"].user
        company = user.company

        is_owner = value.owner_id == company.id
        is_member = ConsortiumMember.objects.filter(
            consortium=value,
            company=company,
            status="active",
        ).exists()
        if not is_owner and not is_member:
            raise serializers.ValidationError(
                "You are not a member of this consortium."
            )
        return value

    def create(self, validated_data):
        """Create assessment and calculate scores."""
        user = self.context["request"].user
        validated_data["company"] = user.company
        assessment = QualityAssessment.objects.create(**validated_data)
        assessment.calculate_scores()
        return assessment


class QualityRuleSerializer(serializers.ModelSerializer):
    """Serializer for QualityRule model."""

    class Meta:
        model = QualityRule
        fields = [
            "id",
            "consortium",
            "name",
            "description",
            "rule_type",
            "metric",
            "condition",
            "severity",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class QualityAlertSerializer(serializers.ModelSerializer):
    """Serializer for QualityAlert model."""

    rule_name = serializers.CharField(source="rule.name", read_only=True)
    severity = serializers.CharField(source="rule.severity", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = QualityAlert
        fields = [
            "id",
            "rule",
            "rule_name",
            "severity",
            "assessment",
            "company",
            "company_name",
            "message",
            "actual_value",
            "expected_value",
            "status",
            "resolved_by",
            "resolution_note",
            "created_at",
            "resolved_at",
        ]
        read_only_fields = [
            "id",
            "rule",
            "assessment",
            "company",
            "message",
            "actual_value",
            "expected_value",
            "created_at",
        ]


class QualityDashboardSerializer(serializers.Serializer):
    """Serializer for quality dashboard summary."""

    total_assessments = serializers.IntegerField()
    average_score = serializers.FloatField()
    open_alerts = serializers.IntegerField()
    active_rules = serializers.IntegerField()
    score_distribution = serializers.DictField()
    recent_assessments = QualityAssessmentSerializer(many=True)
