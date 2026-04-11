"""
Serializers para la app de Consortiums.

Define las representaciones de lectura y escritura para los modelos
Consortium, ConsortiumMember, ContributionProof, TrainingResult
y ConsortiumInvitation.
"""

from django.utils import timezone
from rest_framework import serializers

from .models import (
    Consortium,
    ConsortiumInvitation,
    ConsortiumMember,
    ContributionProof,
    TrainingResult,
)


# -- Consortium ----------------------------------------------------------------


class ConsortiumSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura para un Consortium.

    Incluye campos calculados (member_count, total_records) y el nombre
    de la empresa propietaria como campo anidado de solo lectura.
    """

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
        read_only_fields = [
            "id",
            "owner",
            "status",
            "created_at",
            "updated_at",
        ]


class ConsortiumCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de escritura para crear un Consortium.

    Los campos owner y status se asignan automaticamente en la vista.
    """

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

    def validate_min_members(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "El consorcio requiere al menos 1 miembro."
            )
        return value

    def validate_voting_threshold(self, value):
        if not (0.0 < value <= 1.0):
            raise serializers.ValidationError(
                "El umbral de votacion debe estar entre 0 (exclusivo) y 1 (inclusivo)."
            )
        return value

    def validate_voting_duration_days(self, value):
        if value < 1 or value > 90:
            raise serializers.ValidationError(
                "La duracion de votacion debe estar entre 1 y 90 dias."
            )
        return value

    def validate_model_type(self, value):
        valid = {choice[0] for choice in Consortium.ModelType.choices}
        if value not in valid:
            raise serializers.ValidationError(
                f"Tipo de modelo invalido '{value}'."
            )
        return value


# -- ConsortiumMember ----------------------------------------------------------


class ConsortiumMemberSerializer(serializers.ModelSerializer):
    """
    Serializer para un ConsortiumMember.

    Expone datos de la empresa y del consorcio como campos anidados
    de solo lectura para facilitar el consumo desde el frontend.
    """

    company_name = serializers.CharField(
        source="company.name", read_only=True
    )
    consortium_name = serializers.CharField(
        source="consortium.name", read_only=True
    )

    class Meta:
        model = ConsortiumMember
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "company",
            "company_name",
            "role",
            "status",
            "joined_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "consortium",
            "company",
            "role",
            "status",
            "joined_at",
            "updated_at",
        ]


# -- ContributionProof ---------------------------------------------------------


class ContributionProofSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para ContributionProof.
    """

    company_name = serializers.CharField(
        source="company.name", read_only=True
    )
    consortium_name = serializers.CharField(
        source="consortium.name", read_only=True
    )

    class Meta:
        model = ContributionProof
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "company",
            "company_name",
            "record_count",
            "feature_count",
            "schema_version",
            "data_hash",
            "checksum",
            "verified",
            "verified_at",
            "verification_status",
            "verification_message",
            "blockchain_tx",
            "blockchain_registered_at",
            "created_at",
        ]
        read_only_fields = fields


class ContributionProofCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de escritura para crear un ContributionProof.
    """

    class Meta:
        model = ContributionProof
        fields = [
            "id",
            "consortium",
            "record_count",
            "feature_count",
            "schema_version",
            "data_hash",
            "checksum",
        ]
        read_only_fields = ["id"]


# -- TrainingResult ------------------------------------------------------------


class TrainingResultSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para TrainingResult.
    """

    consortium_name = serializers.CharField(
        source="consortium.name", read_only=True
    )

    class Meta:
        model = TrainingResult
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "status",
            "task_id",
            "model_hash",
            "accuracy",
            "loss",
            "epochs_completed",
            "config_snapshot",
            "contributions_count",
            "total_records",
            "error_message",
            "blockchain_tx",
            "blockchain_registered_at",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields


# -- ConsortiumInvitation ------------------------------------------------------


class ConsortiumInvitationSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura para ConsortiumInvitation.

    Incluye nombres legibles del consorcio, invitador y empresa invitada.
    """

    consortium_name = serializers.CharField(
        source="consortium.name", read_only=True
    )
    inviter_name = serializers.CharField(
        source="inviter.name", read_only=True
    )
    invitee_company_name = serializers.CharField(
        source="invitee_company.name", read_only=True, default=None
    )
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
            "invitee_company_name",
            "role",
            "status",
            "message",
            "is_expired",
            "created_at",
            "expires_at",
            "responded_at",
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
    """
    Serializer de escritura para crear una ConsortiumInvitation.

    Solo acepta los campos que el invitador puede establecer;
    el consorcio, inviter y expires_at se asignan en la vista.
    """

    class Meta:
        model = ConsortiumInvitation
        fields = [
            "id",
            "consortium",
            "invitee_email",
            "role",
            "message",
            "expires_at",
        ]
        read_only_fields = ["id"]

    def validate_role(self, value):
        # No se puede invitar a alguien como owner
        if value == ConsortiumMember.Role.OWNER:
            raise serializers.ValidationError(
                "No se puede asignar el rol 'owner' mediante una invitacion."
            )
        return value

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha de expiracion debe ser futura."
            )
        return value

    def validate(self, attrs):
        consortium = attrs.get("consortium")
        invitee_email = attrs.get("invitee_email")

        # Verificar que no exista una invitacion pendiente duplicada
        if ConsortiumInvitation.objects.filter(
            consortium=consortium,
            invitee_email=invitee_email,
            status=ConsortiumInvitation.Status.PENDING,
        ).exists():
            raise serializers.ValidationError(
                {"invitee_email": "Ya existe una invitacion pendiente para este email en este consorcio."}
            )

        return attrs
