"""
Views para la app de Governance.

ViewSets para gestionar propuestas, votaciones, auditoria,
distribuciones de recompensas y configuracion de gobernanza.
"""

from __future__ import annotations

from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.consortiums.models import Consortium, ConsortiumMember, ContributionProof
from apps.core.permissions import IsCompanyMember, IsConsortiumMember

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import AuditEvent, Proposal, RewardDistribution, Vote
from .serializers import (
    AuditEventSerializer,
    ProposalCreateSerializer,
    ProposalSerializer,
    RewardDistributionCreateSerializer,
    RewardDistributionSerializer,
    VoteCreateSerializer,
    VoteSerializer,
)


# =============================================================================
# GovernanceConfig (read-only, exposes consortium governance settings)
# =============================================================================


class GovernanceConfigSerializer(drf_serializers.Serializer):
    """Serializer para la configuracion de gobernanza de un consorcio."""

    consortium_id = drf_serializers.UUIDField(source="id")
    consortium_name = drf_serializers.CharField(source="name")
    voting_threshold = drf_serializers.FloatField()
    voting_duration_days = drf_serializers.IntegerField()
    min_members = drf_serializers.IntegerField()
    member_count = drf_serializers.IntegerField()
    status = drf_serializers.CharField()


class GovernanceConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Configuracion de gobernanza de un consorcio (solo lectura).

    Expone los ajustes de gobernanza (umbral de votacion, duracion,
    minimo de miembros) para los consorcios donde el usuario participa.

    Filtrar por consortium_id via query param.
    """

    serializer_class = GovernanceConfigSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Retorna consorcios donde el usuario es miembro activo o propietario."""
        user = self.request.user
        if not user.company:
            return Consortium.objects.none()

        company = user.company

        # Consorcios propios
        owned = Consortium.objects.filter(owner=company)

        # Consorcios donde es miembro activo
        member_ids = ConsortiumMember.objects.filter(
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).values_list("consortium_id", flat=True)

        allowed = (owned | Consortium.objects.filter(id__in=member_ids)).distinct()

        # SECURITY: Si se filtra por consortium_id, validar membresía
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return allowed.filter(pk=consortium_id)

        return allowed


# =============================================================================
# Proposals
# =============================================================================


class ProposalViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para propuestas de gobernanza.

    - list:    propuestas filtradas por consortium_id (query param).
    - create:  crea una propuesta para un consorcio.
    - vote:    emitir un voto sobre la propuesta (POST).
    - execute: ejecutar una propuesta aprobada (POST).
    """

    serializer_class = ProposalSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "proposal_type"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "expires_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter proposals by consortium (membership-scoped)."""
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return Proposal.objects.none()

        consortium_id = self.request.query_params.get("consortium_id")
        if not consortium_id:
            return Proposal.objects.none()

        # SECURITY: Verify membership before returning proposals
        is_owner = Consortium.objects.filter(
            pk=consortium_id, owner=company,
        ).exists()
        is_member = ConsortiumMember.objects.filter(
            consortium_id=consortium_id,
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()
        if not is_owner and not is_member:
            return Proposal.objects.none()

        return Proposal.objects.filter(
            consortium_id=consortium_id
        ).select_related("consortium", "proposer").prefetch_related("votes")

    def get_serializer_class(self):
        if self.action == "create":
            return ProposalCreateSerializer
        return ProposalSerializer

    def perform_create(self, serializer):
        """Create proposal and log event."""
        proposal = serializer.save()

        # Create audit event
        AuditEvent.objects.create(
            consortium=proposal.consortium,
            actor=self.request.user.company,
            event_type=AuditEvent.EventType.PROPOSAL_CREATED,
            target_id=str(proposal.id),
            target_type="proposal",
            data={
                "title": proposal.title,
                "type": proposal.proposal_type,
            },
            previous_hash=AuditEvent.get_previous_hash(proposal.consortium_id),
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def vote(self, request, pk=None) -> Response:
        """
        Emitir un voto sobre una propuesta.

        Verifica que la propuesta este activa, que la votacion no haya
        expirado, que el usuario no haya votado ya y que sea miembro del
        consorcio.
        """
        proposal = self.get_object()
        voter = request.user.company

        if not voter:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if proposal is active
        if proposal.status != Proposal.Status.ACTIVE:
            return Response(
                {"detail": "Proposal is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if voting ended
        if proposal.expires_at and timezone.now() > proposal.expires_at:
            return Response(
                {"detail": "Voting period has ended."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already voted
        if Vote.objects.filter(proposal=proposal, voter=voter).exists():
            return Response(
                {"detail": "Already voted on this proposal."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check membership
        membership = ConsortiumMember.objects.filter(
            consortium=proposal.consortium,
            company=voter,
            status=ConsortiumMember.Status.ACTIVE,
        ).first()

        if not membership:
            return Response(
                {"detail": "Not a member of this consortium."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get vote data from request
        support = request.data.get("support")
        comment = request.data.get("comment", "")

        if support not in [choice[0] for choice in Vote.Support.choices]:
            return Response(
                {"detail": "Invalid support value. Use 'for', 'against', or 'abstain'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate voting weight based on contributions
        contributions = ContributionProof.objects.filter(
            consortium=proposal.consortium,
            company=voter,
            verified=True,
        ).aggregate(total=Sum("record_count"))

        weight = max(1, (contributions["total"] or 0) // 100)

        # Create vote
        vote_obj = Vote.objects.create(
            proposal=proposal,
            voter=voter,
            support=support,
            weight=weight,
            comment=comment,
        )

        # Update proposal vote counts
        if vote_obj.support == Vote.Support.FOR:
            proposal.yes_votes += 1
            proposal.voting_weight_yes += weight
        elif vote_obj.support == Vote.Support.AGAINST:
            proposal.no_votes += 1
            proposal.voting_weight_no += weight
        proposal.save(update_fields=[
            "yes_votes", "no_votes", "voting_weight_yes", "voting_weight_no",
        ])

        # Create audit event
        AuditEvent.objects.create(
            consortium=proposal.consortium,
            actor=voter,
            event_type=AuditEvent.EventType.VOTE_CAST,
            target_id=str(proposal.id),
            target_type="proposal",
            data={
                "support": vote_obj.support,
                "weight": float(weight),
            },
            previous_hash=AuditEvent.get_previous_hash(proposal.consortium_id),
        )

        return Response(VoteSerializer(vote_obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def execute(self, request, pk=None) -> Response:
        """
        Ejecutar una propuesta despues de que termine la votacion.

        Verifica que la propuesta este activa, que la votacion haya terminado,
        calcula el resultado y ejecuta la accion si fue aprobada.
        """
        from .services import ProposalExecutionService

        proposal = self.get_object()

        # Check if still active
        if proposal.status != Proposal.Status.ACTIVE:
            return Response(
                {"detail": f"Proposal is already {proposal.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if voting ended
        if proposal.expires_at and timezone.now() < proposal.expires_at:
            return Response(
                {"detail": "Voting period has not ended yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate result
        consortium = proposal.consortium
        total_weight = proposal.voting_weight_yes + proposal.voting_weight_no

        if total_weight == 0:
            proposal.status = Proposal.Status.REJECTED
            proposal.executed_at = timezone.now()
            proposal.save(update_fields=["status", "executed_at"])
            message = "No votes cast. Proposal rejected."
            passed = False
        else:
            approval_ratio = float(proposal.voting_weight_yes) / float(total_weight)
            passed = approval_ratio >= consortium.voting_threshold

            if passed:
                proposal.status = Proposal.Status.PASSED
                proposal.save(update_fields=["status"])
                execution_service = ProposalExecutionService()
                result = execution_service.execute(proposal)
                proposal.refresh_from_db()
                if result.success and result.data:
                    message = result.data.message
                elif not result.success:
                    message = result.error or "Proposal passed but execution failed."
                else:
                    message = "Proposal passed and executed."
            else:
                proposal.status = Proposal.Status.REJECTED
                proposal.executed_at = timezone.now()
                proposal.save(update_fields=["status", "executed_at"])
                message = "Proposal rejected."

        # Create audit event
        AuditEvent.objects.create(
            consortium=proposal.consortium,
            actor=request.user.company,
            event_type=AuditEvent.EventType.PROPOSAL_EXECUTED,
            target_id=str(proposal.id),
            target_type="proposal",
            data={
                "passed": passed,
                "yes_votes": proposal.yes_votes,
                "no_votes": proposal.no_votes,
            },
            previous_hash=AuditEvent.get_previous_hash(proposal.consortium_id),
        )

        return Response({
            "detail": message,
            "passed": passed,
            "status": proposal.status,
            "yes_votes": proposal.yes_votes,
            "no_votes": proposal.no_votes,
        })

    def _apply_proposal(self, proposal: "Proposal", consortium) -> None:
        """Apply a passed proposal's action to the consortium."""
        from apps.consortiums.models import Consortium as ConsortiumModel

        data = proposal.data or {}
        proposal_type = proposal.proposal_type

        if proposal_type == Proposal.Type.UPDATE_CONFIG:
            # Update consortium config fields from the proposal data
            config = data.get("config", {})
            update_fields = []
            for field, value in config.items():
                if hasattr(consortium, field):
                    setattr(consortium, field, value)
                    update_fields.append(field)
            if update_fields:
                consortium.save(update_fields=update_fields + ["updated_at"])

    @action(detail=True, methods=["get"])
    def votes(self, request, pk=None) -> Response:
        """Listar todos los votos de una propuesta."""
        proposal = self.get_object()
        proposal_votes = Vote.objects.filter(proposal=proposal)
        serializer = VoteSerializer(proposal_votes, many=True)
        return Response(serializer.data)


# =============================================================================
# Votes (standalone endpoint for POST /votes/)
# =============================================================================


class VoteViewSet(viewsets.GenericViewSet):
    """
    Standalone endpoint for casting votes.

    POST /votes/ — cast a vote on a proposal (equivalent to proposals/{pk}/vote/).
    """

    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return Vote.objects.none()
        return Vote.objects.filter(voter=company)

    def create(self, request, *args, **kwargs):
        """Cast a vote on a proposal."""
        from rest_framework import mixins

        voter = request.user.company
        if not voter:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proposal_id = request.data.get("proposal")
        if not proposal_id:
            return Response(
                {"detail": "proposal is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            proposal = Proposal.objects.get(id=proposal_id)
        except Proposal.DoesNotExist:
            return Response(
                {"detail": "Proposal not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Delegate to the proposal's vote action logic
        if proposal.status != Proposal.Status.ACTIVE:
            return Response(
                {"detail": "Proposal is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if proposal.expires_at and timezone.now() > proposal.expires_at:
            return Response(
                {"detail": "Voting period has ended."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Vote.objects.filter(proposal=proposal, voter=voter).exists():
            return Response(
                {"detail": "Already voted on this proposal."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership = ConsortiumMember.objects.filter(
            consortium=proposal.consortium,
            company=voter,
            status=ConsortiumMember.Status.ACTIVE,
        ).first()

        if not membership:
            return Response(
                {"detail": "Not a member of this consortium."},
                status=status.HTTP_403_FORBIDDEN,
            )

        support = request.data.get("support")
        comment = request.data.get("comment", "")

        # Map boolean support to Vote.Support choices
        if isinstance(support, bool):
            support = Vote.Support.FOR if support else Vote.Support.AGAINST

        if support not in [choice[0] for choice in Vote.Support.choices]:
            return Response(
                {"detail": "Invalid support value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contributions = ContributionProof.objects.filter(
            consortium=proposal.consortium,
            company=voter,
            verified=True,
        ).aggregate(total=Sum("record_count"))

        weight = max(1, (contributions["total"] or 0) // 100)

        vote_obj = Vote.objects.create(
            proposal=proposal,
            voter=voter,
            support=support,
            weight=weight,
            comment=comment,
        )

        if vote_obj.support == Vote.Support.FOR:
            proposal.yes_votes += 1
            proposal.voting_weight_yes += weight
        elif vote_obj.support == Vote.Support.AGAINST:
            proposal.no_votes += 1
            proposal.voting_weight_no += weight
        proposal.save(update_fields=[
            "yes_votes", "no_votes", "voting_weight_yes", "voting_weight_no",
        ])

        AuditEvent.objects.create(
            consortium=proposal.consortium,
            actor=voter,
            event_type=AuditEvent.EventType.VOTE_CAST,
            target_id=str(proposal.id),
            target_type="proposal",
            data={"support": vote_obj.support, "weight": float(weight)},
            previous_hash=AuditEvent.get_previous_hash(proposal.consortium_id),
        )

        return Response(VoteSerializer(vote_obj).data, status=status.HTTP_201_CREATED)


# =============================================================================
# Audit Events
# =============================================================================


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para eventos de auditoria.
    """

    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["event_type", "target_type"]
    ordering_fields = ["created_at", "event_type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter audit events by consortium (membership-scoped)."""
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return AuditEvent.objects.none()

        consortium_id = self.request.query_params.get("consortium_id")
        if not consortium_id:
            return AuditEvent.objects.none()

        # SECURITY: Verify membership before returning audit events
        is_owner = Consortium.objects.filter(
            pk=consortium_id, owner=company,
        ).exists()
        is_member = ConsortiumMember.objects.filter(
            consortium_id=consortium_id,
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()
        if not is_owner and not is_member:
            return AuditEvent.objects.none()

        queryset = AuditEvent.objects.filter(
            consortium_id=consortium_id
        ).select_related("consortium", "actor")

        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return queryset.order_by("-created_at")

    @action(detail=False, methods=["get"])
    def verify(self, request) -> Response:
        """Verificar la integridad de la cadena de auditoria."""
        consortium_id = request.query_params.get("consortium_id")
        if not consortium_id:
            return Response(
                {"detail": "consortium_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # SECURITY: Verify membership before allowing audit verification
        company = getattr(request.user, "company", None)
        if not company:
            return Response(
                {"detail": "No tienes acceso a este consorcio."},
                status=status.HTTP_403_FORBIDDEN,
            )
        is_owner = Consortium.objects.filter(
            pk=consortium_id, owner=company,
        ).exists()
        is_member = ConsortiumMember.objects.filter(
            consortium_id=consortium_id,
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()
        if not is_owner and not is_member:
            return Response(
                {"detail": "No tienes acceso a este consorcio."},
                status=status.HTTP_403_FORBIDDEN,
            )

        events = AuditEvent.objects.filter(consortium_id=consortium_id).order_by("created_at")

        is_valid = True
        previous_hash = ""

        for event in events:
            if event.previous_hash != previous_hash:
                is_valid = False
                break
            previous_hash = event.event_hash

        return Response({
            "consortium_id": consortium_id,
            "valid": is_valid,
            "event_count": events.count(),
            "verified_at": timezone.now(),
        })


# =============================================================================
# Reward Distributions
# =============================================================================


class RewardDistributionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para distribuciones de recompensas.
    """

    serializer_class = RewardDistributionSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter distributions by consortium (membership-scoped)."""
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return RewardDistribution.objects.none()

        consortium_id = self.request.query_params.get("consortium_id")
        if not consortium_id:
            return RewardDistribution.objects.none()

        # SECURITY: Verify membership before returning distributions
        is_owner = Consortium.objects.filter(
            pk=consortium_id, owner=company,
        ).exists()
        is_member = ConsortiumMember.objects.filter(
            consortium_id=consortium_id,
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()
        if not is_owner and not is_member:
            return RewardDistribution.objects.none()

        return RewardDistribution.objects.filter(consortium_id=consortium_id)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsCompanyMember])
    @transaction.atomic
    def distribute(self, request) -> Response:
        """Distribuir recompensas a miembros del consorcio."""
        serializer = RewardDistributionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consortium_id = serializer.validated_data["consortium_id"]
        amount = serializer.validated_data["amount"]

        # SECURITY: Verify membership before distributing rewards
        company = getattr(request.user, "company", None)
        if not company:
            return Response(
                {"detail": "No tienes acceso a este consorcio."},
                status=status.HTTP_403_FORBIDDEN,
            )
        is_owner = Consortium.objects.filter(
            pk=consortium_id, owner=company,
        ).exists()
        is_member = ConsortiumMember.objects.filter(
            consortium_id=consortium_id,
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()
        if not is_owner and not is_member:
            return Response(
                {"detail": "No tienes acceso a este consorcio."},
                status=status.HTTP_403_FORBIDDEN,
            )

        contributions = (
            ContributionProof.objects.filter(
                consortium_id=consortium_id,
                verified=True,
            )
            .values("company_id")
            .annotate(total_records=Sum("record_count"))
        )

        total_records = sum(c["total_records"] for c in contributions)

        if total_records == 0:
            return Response(
                {"detail": "No contributions to distribute rewards."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        distributions = []
        for contrib in contributions:
            weight = contrib["total_records"] / total_records
            share = float(amount) * weight
            distributions.append({
                "company_id": str(contrib["company_id"]),
                "amount": round(share, 8),
                "weight": round(weight * 100, 2),
            })

        distribution = RewardDistribution.objects.create(
            consortium_id=consortium_id,
            total_amount=amount,
            distributions=distributions,
        )

        AuditEvent.objects.create(
            consortium_id=consortium_id,
            actor=request.user.company,
            event_type=AuditEvent.EventType.REWARD_DISTRIBUTED,
            target_id=str(distribution.id),
            target_type="reward_distribution",
            data={
                "total_amount": str(amount),
                "recipient_count": len(distributions),
            },
            previous_hash=AuditEvent.get_previous_hash(consortium_id),
        )

        return Response(
            RewardDistributionSerializer(distribution).data,
            status=status.HTTP_201_CREATED,
        )
