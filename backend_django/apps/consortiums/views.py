"""
Consortium views for Xcapit FHE-ML Platform.

Provides endpoints for consortium management, membership,
and contribution tracking.
"""

from apps.core.models import AuditLog
from apps.core.permissions import (
    IsCompanyMember,
    IsConsortiumAdmin,
    IsConsortiumMember,
    IsConsortiumOwner,
)
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Consortium, ConsortiumInvitation, ConsortiumMember, ContributionProof
from .serializers import (
    ConsortiumCreateSerializer,
    ConsortiumInvitationCreateSerializer,
    ConsortiumInvitationSerializer,
    ConsortiumMemberSerializer,
    ConsortiumSerializer,
    ConsortiumStatsSerializer,
    ContributionProofCreateSerializer,
    ContributionProofSerializer,
)


class ConsortiumViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Consortium management.
    """

    serializer_class = ConsortiumSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "model_type"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Return consortiums the user's company is a member of.
        """
        user = self.request.user
        if not user.company:
            return Consortium.objects.none()

        # Get consortiums where company is a member
        member_consortiums = ConsortiumMember.objects.filter(
            company=user.company,
            status=ConsortiumMember.Status.ACTIVE,
        ).values_list("consortium_id", flat=True)

        return Consortium.objects.filter(id__in=member_consortiums).select_related(
            "owner"
        ).prefetch_related("members")

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == "create":
            return ConsortiumCreateSerializer
        return ConsortiumSerializer

    def get_permissions(self):
        """Apply different permissions for different actions."""
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsConsortiumOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create consortium and log event."""
        consortium = serializer.save()

        # Log creation
        AuditLog.log(
            self.request,
            action="consortium_created",
            resource_type="consortium",
            resource_id=consortium.id,
            extra_data={"name": consortium.name},
        )

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get consortium statistics."""
        consortium = self.get_object()

        members = ConsortiumMember.objects.filter(consortium=consortium)
        contributions = ContributionProof.objects.filter(
            consortium=consortium, verified=True
        )

        stats = {
            "total_members": members.count(),
            "active_members": members.filter(status=ConsortiumMember.Status.ACTIVE).count(),
            "total_records": contributions.aggregate(total=Sum("record_count"))["total"] or 0,
            "total_contributions": contributions.count(),
            "model_status": consortium.status,
        }

        serializer = ConsortiumStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsConsortiumAdmin])
    def start_training(self, request, pk=None):
        """Start consortium model training."""
        from .services.training import FHETrainingService

        consortium = self.get_object()

        if consortium.status != Consortium.Status.ACTIVE:
            return Response(
                {"detail": "Consortium must be active to start training."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check minimum members
        active_members = ConsortiumMember.objects.filter(
            consortium=consortium,
            status=ConsortiumMember.Status.ACTIVE,
        ).count()

        if active_members < consortium.min_members:
            return Response(
                {"detail": f"Need at least {consortium.min_members} members to start training."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Start training via service
        training_service = FHETrainingService(request=request)
        result = training_service.start_training(consortium)

        if not result.success:
            return Response(
                {"detail": result.error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Log event
        AuditLog.log(
            request,
            action="training_started",
            resource_type="consortium",
            resource_id=consortium.id,
            extra_data={
                "task_id": result.data.get("task_id"),
                "training_result_id": result.data.get("training_result_id"),
            },
        )

        return Response({
            "detail": "Training started.",
            "status": "training",
            "task_id": result.data.get("task_id"),
            "training_result_id": result.data.get("training_result_id"),
            "contributions_count": result.data.get("contributions_count"),
            "total_records": result.data.get("total_records"),
        })

    @action(detail=False, methods=["get"])
    def owned(self, request):
        """Get consortiums owned by the user's company."""
        user = request.user
        if not user.company:
            return Response([])

        consortiums = Consortium.objects.filter(owner=user.company)
        serializer = self.get_serializer(consortiums, many=True)
        return Response(serializer.data)


class ConsortiumMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for consortium membership management.
    """

    serializer_class = ConsortiumMemberSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "role"]
    ordering_fields = ["joined_at", "role", "status"]
    ordering = ["-joined_at"]

    def get_queryset(self):
        """Filter members by consortium."""
        consortium_id = self.kwargs.get("consortium_pk")
        return ConsortiumMember.objects.filter(
            consortium_id=consortium_id
        ).select_related("company", "consortium")

    def get_permissions(self):
        """Only admins can modify memberships."""
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsConsortiumAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsConsortiumAdmin])
    def approve(self, request, consortium_pk=None, pk=None):
        """Approve a pending membership."""
        member = self.get_object()

        if member.status != ConsortiumMember.Status.PENDING:
            return Response(
                {"detail": "Membership is not pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.status = ConsortiumMember.Status.ACTIVE
        member.save(update_fields=["status", "updated_at"])

        # Log event
        AuditLog.log(
            request,
            action="member_approved",
            resource_type="consortium_member",
            resource_id=member.id,
            extra_data={"company_id": str(member.company_id)},
        )

        return Response(ConsortiumMemberSerializer(member).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsConsortiumAdmin])
    def remove(self, request, consortium_pk=None, pk=None):
        """Remove a member from the consortium."""
        member = self.get_object()

        if member.role == ConsortiumMember.Role.OWNER:
            return Response(
                {"detail": "Cannot remove the consortium owner."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.status = ConsortiumMember.Status.REMOVED
        member.save(update_fields=["status", "updated_at"])

        # Log event
        AuditLog.log(
            request,
            action="member_removed",
            resource_type="consortium_member",
            resource_id=member.id,
            extra_data={"company_id": str(member.company_id)},
        )

        return Response({"detail": "Member removed."})

    @action(detail=False, methods=["post"])
    def leave(self, request, consortium_pk=None):
        """Leave a consortium."""
        user = request.user
        member = ConsortiumMember.objects.filter(
            consortium_id=consortium_pk,
            company=user.company,
        ).first()

        if not member:
            return Response(
                {"detail": "Not a member of this consortium."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if member.role == ConsortiumMember.Role.OWNER:
            return Response(
                {"detail": "Owner cannot leave. Transfer ownership first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.status = ConsortiumMember.Status.LEFT
        member.save(update_fields=["status", "updated_at"])

        # Log event
        AuditLog.log(
            request,
            action="member_left",
            resource_type="consortium_member",
            resource_id=member.id,
        )

        return Response({"detail": "Left consortium successfully."})


class ContributionProofViewSet(viewsets.ModelViewSet):
    """
    ViewSet for contribution proof management.
    """

    serializer_class = ContributionProofSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["verified", "company"]
    ordering_fields = ["created_at", "record_count", "verified"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter contributions by consortium."""
        consortium_id = self.kwargs.get("consortium_pk")
        return ContributionProof.objects.filter(
            consortium_id=consortium_id
        ).select_related("company", "consortium")

    def get_serializer_class(self):
        if self.action == "create":
            return ContributionProofCreateSerializer
        return ContributionProofSerializer

    def perform_create(self, serializer):
        """Create contribution and log event."""
        contribution = serializer.save()

        # Log event
        AuditLog.log(
            self.request,
            action="data_contributed",
            resource_type="contribution_proof",
            resource_id=contribution.id,
            extra_data={
                "record_count": contribution.record_count,
                "data_hash": contribution.data_hash[:16] + "...",
            },
        )

    @action(detail=False, methods=["get"])
    def my_contributions(self, request, consortium_pk=None):
        """Get current company's contributions."""
        user = request.user
        contributions = ContributionProof.objects.filter(
            consortium_id=consortium_pk,
            company=user.company,
        )
        serializer = self.get_serializer(contributions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request, consortium_pk=None):
        """Get contribution summary per company."""
        contributions = (
            ContributionProof.objects.filter(consortium_id=consortium_pk, verified=True)
            .values("company__id", "company__name")
            .annotate(
                total_records=Sum("record_count"),
                contribution_count=Count("id"),
            )
            .order_by("-total_records")
        )

        return Response(list(contributions))


class ConsortiumInvitationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for consortium invitations.
    """

    serializer_class = ConsortiumInvitationSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Get invitations for the user's company."""
        user = self.request.user
        if not user.company:
            return ConsortiumInvitation.objects.none()

        # Sent or received invitations
        return ConsortiumInvitation.objects.filter(
            inviter=user.company,
        ) | ConsortiumInvitation.objects.filter(invitee_email=user.company.email)

    def get_serializer_class(self):
        if self.action == "create":
            return ConsortiumInvitationCreateSerializer
        return ConsortiumInvitationSerializer

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def accept(self, request, pk=None):
        """Accept an invitation."""
        invitation = self.get_object()
        user = request.user

        if invitation.invitee_email.lower() != user.company.email.lower():
            return Response(
                {"detail": "This invitation is not for your company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != ConsortiumInvitation.Status.PENDING:
            return Response(
                {"detail": "Invitation is no longer pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.is_expired:
            return Response(
                {"detail": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create membership
        ConsortiumMember.objects.create(
            consortium=invitation.consortium,
            company=user.company,
            role=invitation.role,
            status=ConsortiumMember.Status.ACTIVE,
        )

        # Update invitation
        invitation.status = ConsortiumInvitation.Status.ACCEPTED
        invitation.invitee_company = user.company
        invitation.responded_at = timezone.now()
        invitation.save()

        # Log event
        AuditLog.log(
            request,
            action="invitation_accepted",
            resource_type="consortium_invitation",
            resource_id=invitation.id,
        )

        return Response({"detail": "Invitation accepted."})

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        """Decline an invitation."""
        invitation = self.get_object()
        user = request.user

        if invitation.invitee_email.lower() != user.company.email.lower():
            return Response(
                {"detail": "This invitation is not for your company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != ConsortiumInvitation.Status.PENDING:
            return Response(
                {"detail": "Invitation is no longer pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation.status = ConsortiumInvitation.Status.DECLINED
        invitation.responded_at = timezone.now()
        invitation.save()

        return Response({"detail": "Invitation declined."})

    @action(detail=False, methods=["get"])
    def received(self, request):
        """Get received invitations."""
        user = request.user
        invitations = ConsortiumInvitation.objects.filter(
            invitee_email=user.company.email,
            status=ConsortiumInvitation.Status.PENDING,
        )
        serializer = self.get_serializer(invitations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def sent(self, request):
        """Get sent invitations."""
        user = request.user
        invitations = ConsortiumInvitation.objects.filter(inviter=user.company)
        serializer = self.get_serializer(invitations, many=True)
        return Response(serializer.data)
