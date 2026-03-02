"""
Governance views for Xcapit FHE-ML Platform.

Provides endpoints for proposals, voting, audit trail, and rewards.
"""

from apps.consortiums.models import ConsortiumMember, ContributionProof
from apps.core.permissions import IsCompanyMember, IsConsortiumMember, IsConsortiumOwner
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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


class ProposalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for governance proposals.
    """

    serializer_class = ProposalSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "proposal_type"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "expires_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter proposals by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return Proposal.objects.filter(
                consortium_id=consortium_id
            ).select_related("consortium", "proposer").prefetch_related("votes")
        return Proposal.objects.none()

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

    @action(detail=True, methods=["get"])
    def votes(self, request, pk=None):
        """Get all votes for a proposal."""
        proposal = self.get_object()
        votes = Vote.objects.filter(proposal=proposal)
        serializer = VoteSerializer(votes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def execute(self, request, pk=None):
        """Execute a proposal after voting ends."""
        proposal = self.get_object()

        # Check if still active
        if proposal.status != Proposal.Status.ACTIVE:
            return Response(
                {"detail": f"Proposal is already {proposal.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if voting ended
        if timezone.now() < proposal.expires_at:
            return Response(
                {"detail": "Voting period has not ended yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate result
        consortium = proposal.consortium
        passed = proposal.check_result(threshold=consortium.voting_threshold)

        if passed is None:
            proposal.status = Proposal.Status.REJECTED
            message = "No votes cast."
            proposal.executed_at = timezone.now()
            proposal.save()
        elif passed:
            proposal.status = Proposal.Status.PASSED
            proposal.save(update_fields=["status"])

            # Execute proposal action based on type
            from .services import ProposalExecutionService

            execution_service = ProposalExecutionService(request=request)
            result = execution_service.execute(proposal)

            if result.success:
                message = f"Proposal passed and executed: {result.data.message}"
            else:
                message = f"Proposal passed but execution failed: {result.error}"
        else:
            proposal.status = Proposal.Status.REJECTED
            message = "Proposal rejected."
            proposal.executed_at = timezone.now()
            proposal.save()

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


class VoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for casting votes.
    """

    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    http_method_names = ["get", "post"]  # No updates or deletes

    def get_queryset(self):
        """Filter votes by user's company."""
        user = self.request.user
        if user.company:
            return Vote.objects.filter(voter=user.company).select_related(
                "proposal", "voter"
            )
        return Vote.objects.none()

    def get_permissions(self):
        """Vote creation validates consortium membership internally."""
        if self.action == "create":
            return [IsAuthenticated(), IsCompanyMember()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return VoteCreateSerializer
        return VoteSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Cast a vote on a proposal."""
        serializer = VoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proposal = Proposal.objects.get(id=serializer.validated_data["proposal"].id)
        voter = request.user.company

        # Check if proposal is active
        if proposal.status != Proposal.Status.ACTIVE:
            return Response(
                {"detail": "Proposal is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if voting ended
        if timezone.now() > proposal.expires_at:
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

        # Calculate voting weight based on contributions
        contributions = ContributionProof.objects.filter(
            consortium=proposal.consortium,
            company=voter,
            verified=True,
        ).aggregate(total=Sum("record_count"))

        weight = max(1, (contributions["total"] or 0) // 100)  # 1 weight per 100 records

        # Create vote
        vote = Vote.objects.create(
            proposal=proposal,
            voter=voter,
            support=serializer.validated_data["support"],
            weight=weight,
            comment=serializer.validated_data.get("comment", ""),
        )

        # Update proposal vote counts
        if vote.support:
            proposal.yes_votes += 1
            proposal.voting_weight_yes += weight
        else:
            proposal.no_votes += 1
            proposal.voting_weight_no += weight
        proposal.save()

        # Create audit event
        AuditEvent.objects.create(
            consortium=proposal.consortium,
            actor=voter,
            event_type=AuditEvent.EventType.PROPOSAL_VOTED,
            target_id=str(proposal.id),
            target_type="proposal",
            data={
                "support": vote.support,
                "weight": weight,
            },
            previous_hash=AuditEvent.get_previous_hash(proposal.consortium_id),
        )

        return Response(VoteSerializer(vote).data, status=status.HTTP_201_CREATED)


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit events (read-only).
    """

    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["event_type", "target_type"]
    ordering_fields = ["created_at", "event_type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter audit events by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            queryset = AuditEvent.objects.filter(
                consortium_id=consortium_id
            ).select_related("consortium", "actor")

            # Optional filters
            event_type = self.request.query_params.get("event_type")
            if event_type:
                queryset = queryset.filter(event_type=event_type)

            return queryset.order_by("-created_at")
        return AuditEvent.objects.none()

    @action(detail=False, methods=["get"])
    def verify(self, request):
        """Verify audit trail integrity."""
        consortium_id = request.query_params.get("consortium_id")
        if not consortium_id:
            return Response(
                {"detail": "consortium_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
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


class RewardDistributionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reward distributions.
    """

    serializer_class = RewardDistributionSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter distributions by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return RewardDistribution.objects.filter(consortium_id=consortium_id)
        return RewardDistribution.objects.none()

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsConsortiumOwner])
    @transaction.atomic
    def distribute(self, request):
        """Distribute rewards to consortium members."""
        serializer = RewardDistributionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consortium_id = serializer.validated_data["consortium_id"]
        amount = serializer.validated_data["amount"]

        # Get contribution summary
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

        # Calculate distributions
        distributions = []
        for contrib in contributions:
            weight = contrib["total_records"] / total_records
            share = float(amount) * weight
            distributions.append({
                "company_id": str(contrib["company_id"]),
                "amount": round(share, 8),
                "weight": round(weight * 100, 2),
            })

        # Create distribution record
        distribution = RewardDistribution.objects.create(
            consortium_id=consortium_id,
            total_amount=amount,
            distributions=distributions,
        )

        # Create audit event
        AuditEvent.objects.create(
            consortium_id=consortium_id,
            actor=request.user.company,
            event_type=AuditEvent.EventType.REWARDS_DISTRIBUTED,
            target_id=str(distribution.id),
            target_type="reward_distribution",
            data={
                "total_amount": str(amount),
                "recipient_count": len(distributions),
            },
            previous_hash=AuditEvent.get_previous_hash(consortium_id),
        )

        return Response(RewardDistributionSerializer(distribution).data, status=status.HTTP_201_CREATED)
