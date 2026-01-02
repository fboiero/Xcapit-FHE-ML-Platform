"""
Consortium serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import Consortium, ConsortiumInvitation, ConsortiumMember, ContributionProof


class ConsortiumSerializer(serializers.ModelSerializer):
    """Serializer for Consortium model."""

    owner_name = serializers.CharField(source="owner.name", read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    total_records = serializers.IntegerField(read_only=True)

    class Meta:
        model = Consortium
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "owner_name",
            "model_type",
            "status",
            "ml_config",
            "min_members",
            "voting_threshold",
            "voting_duration_days",
            "member_count",
            "total_records",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "status", "created_at", "updated_at"]


class ConsortiumCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Consortium."""

    class Meta:
        model = Consortium
        fields = [
            "id",
            "name",
            "description",
            "model_type",
            "ml_config",
            "min_members",
            "voting_threshold",
            "voting_duration_days",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        """Validate consortium name."""
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        return value

    def validate_voting_threshold(self, value):
        """Validate voting threshold is between 0 and 1."""
        if not 0 < value <= 1:
            raise serializers.ValidationError("Voting threshold must be between 0 and 1.")
        return value

    def validate_ml_config(self, value):
        """Validate ML configuration."""
        allowed_keys = {
            "learning_rate",
            "epochs",
            "batch_size",
            "security_level",
            "poly_modulus_degree",
        }
        for key in value.keys():
            if key not in allowed_keys:
                raise serializers.ValidationError(f"Invalid config key: {key}")
        return value

    def create(self, validated_data):
        """Create consortium with owner and initial membership."""
        owner = self.context["request"].user.company
        consortium = Consortium.objects.create(owner=owner, **validated_data)

        # Create owner membership
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=owner,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        return consortium


class ConsortiumMemberSerializer(serializers.ModelSerializer):
    """Serializer for ConsortiumMember model."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_email = serializers.CharField(source="company.email", read_only=True)

    class Meta:
        model = ConsortiumMember
        fields = [
            "id",
            "consortium",
            "company",
            "company_name",
            "company_email",
            "role",
            "status",
            "joined_at",
            "updated_at",
        ]
        read_only_fields = ["id", "consortium", "company", "joined_at", "updated_at"]


class ContributionProofSerializer(serializers.ModelSerializer):
    """Serializer for ContributionProof model."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = ContributionProof
        fields = [
            "id",
            "consortium",
            "company",
            "company_name",
            "record_count",
            "feature_count",
            "data_hash",
            "checksum",
            "verified",
            "verified_at",
            "blockchain_tx",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "verified",
            "verified_at",
            "blockchain_tx",
            "created_at",
        ]


class ContributionProofCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a ContributionProof."""

    class Meta:
        model = ContributionProof
        fields = [
            "id",
            "consortium",
            "record_count",
            "feature_count",
            "data_hash",
            "checksum",
        ]
        read_only_fields = ["id"]

    def validate_record_count(self, value):
        """Validate record count is positive."""
        if value < 1:
            raise serializers.ValidationError("Record count must be at least 1.")
        return value

    def validate_data_hash(self, value):
        """Validate data hash format (SHA-256)."""
        if len(value) != 64 or not all(c in "0123456789abcdef" for c in value.lower()):
            raise serializers.ValidationError("Invalid SHA-256 hash format.")
        return value.lower()

    def create(self, validated_data):
        """Create contribution proof."""
        company = self.context["request"].user.company
        return ContributionProof.objects.create(company=company, **validated_data)


class ConsortiumInvitationSerializer(serializers.ModelSerializer):
    """Serializer for ConsortiumInvitation model."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    inviter_name = serializers.CharField(source="inviter.name", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ConsortiumInvitation
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "inviter",
            "inviter_name",
            "invitee_email",
            "invitee_company",
            "role",
            "status",
            "message",
            "created_at",
            "expires_at",
            "responded_at",
            "is_expired",
        ]
        read_only_fields = [
            "id",
            "inviter",
            "invitee_company",
            "status",
            "created_at",
            "responded_at",
        ]


class ConsortiumInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a ConsortiumInvitation."""

    class Meta:
        model = ConsortiumInvitation
        fields = ["id", "consortium", "invitee_email", "role", "message", "expires_at"]
        read_only_fields = ["id"]

    def validate_invitee_email(self, value):
        """Validate email and check not already a member."""
        value = value.lower()
        consortium = self.initial_data.get("consortium")

        # Check if already a member
        from apps.core.models import Company

        company = Company.objects.filter(email=value).first()
        if company:
            existing = ConsortiumMember.objects.filter(
                consortium_id=consortium,
                company=company,
            ).exists()
            if existing:
                raise serializers.ValidationError("Company is already a member.")

        return value

    def create(self, validated_data):
        """Create invitation."""
        inviter = self.context["request"].user.company
        return ConsortiumInvitation.objects.create(inviter=inviter, **validated_data)


class ConsortiumStatsSerializer(serializers.Serializer):
    """Serializer for consortium statistics."""

    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    total_records = serializers.IntegerField()
    total_contributions = serializers.IntegerField()
    model_status = serializers.CharField()
