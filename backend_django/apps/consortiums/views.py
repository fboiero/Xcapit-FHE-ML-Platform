"""
Views para la app de Consortiums.

ViewSets y APIViews para gestionar consorcios, membresías,
pruebas de contribución, resultados de entrenamiento e invitaciones.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsCompanyMember, IsConsortiumMember

from .models import (
    Consortium,
    ConsortiumInvitation,
    ConsortiumMember,
    ContributionProof,
    TrainingResult,
)
from .serializers import (
    ConsortiumCreateSerializer,
    ConsortiumInvitationCreateSerializer,
    ConsortiumInvitationSerializer,
    ConsortiumMemberSerializer,
    ConsortiumSerializer,
    ContributionProofCreateSerializer,
    ContributionProofSerializer,
    TrainingResultSerializer,
)


# =============================================================================
# Consortium CRUD
# =============================================================================


class ConsortiumViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para Consortium.

    - list:   consorcios donde la empresa del usuario es owner o miembro activo.
    - create: crea un consorcio y registra a la empresa como owner.
    - update/partial_update: solo el owner puede modificar.
    - destroy: solo el owner puede eliminar (soft: cambia status a archived).
    """

    serializer_class = ConsortiumSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Retorna consorcios donde la empresa es propietaria o miembro activo."""
        user = self.request.user
        if not user.company:
            return Consortium.objects.none()

        company = user.company

        # Consorcios propios
        owned = Consortium.objects.filter(owner=company)

        # Consorcios donde la empresa es miembro activo
        member_consortium_ids = ConsortiumMember.objects.filter(
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).values_list("consortium_id", flat=True)

        return (owned | Consortium.objects.filter(id__in=member_consortium_ids)).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return ConsortiumCreateSerializer
        return ConsortiumSerializer

    def perform_create(self, serializer):
        """Crea el consorcio asignando la empresa del usuario como owner
        y lo registra automaticamente como miembro con rol owner."""
        company = self.request.user.company
        consortium = serializer.save(owner=company)

        # Registrar al owner como miembro activo
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

    def perform_update(self, serializer):
        """Solo el owner puede actualizar el consorcio."""
        consortium = self.get_object()
        if consortium.owner_id != self.request.user.company_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo el propietario puede editar este consorcio.")
        serializer.save()

    def perform_destroy(self, instance):
        """Archiva el consorcio en lugar de eliminarlo fisicamente."""
        if instance.owner_id != self.request.user.company_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo el propietario puede eliminar este consorcio.")
        instance.status = Consortium.Status.ARCHIVED
        instance.save(update_fields=["status", "updated_at"])

    @action(detail=False, methods=["get"])
    def owned(self, request):
        """List consortiums owned by the current company."""
        company = request.user.company
        if not company:
            return Response({"detail": "No company associated."}, status=status.HTTP_403_FORBIDDEN)
        qs = Consortium.objects.filter(owner=company)
        serializer = ConsortiumSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Return aggregate stats for a consortium."""
        consortium = self.get_object()
        total_members = ConsortiumMember.objects.filter(consortium=consortium).count()
        active_members = ConsortiumMember.objects.filter(
            consortium=consortium, status=ConsortiumMember.Status.ACTIVE
        ).count()
        total_contributions = ContributionProof.objects.filter(consortium=consortium).count()
        return Response(
            {
                "total_members": total_members,
                "active_members": active_members,
                "total_contributions": total_contributions,
                "status": consortium.status,
                "name": consortium.name,
            }
        )

    @action(detail=True, methods=["post"])
    def start_training(self, request, pk=None):
        """Initiate federated training for this consortium."""
        from apps.consortiums.services.training import FHETrainingService

        consortium = self.get_object()
        if consortium.status != Consortium.Status.ACTIVE:
            return Response(
                {"detail": "Consortium must be active to start training."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        active_members = ConsortiumMember.objects.filter(
            consortium=consortium, status=ConsortiumMember.Status.ACTIVE
        ).count()
        min_members = getattr(consortium, "min_members", 2) or 2
        if active_members < min_members:
            return Response(
                {"detail": f"Need at least {min_members} active members to start training."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        service = FHETrainingService(request=request)
        result = service.start_training(consortium)
        if not result.success:
            return Response(
                {"detail": result.error, "error_code": result.error_code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({
            "detail": "Training initiated.",
            "consortium_id": str(consortium.id),
            "task_id": result.data.get("task_id"),
            "training_result_id": result.data.get("training_result_id"),
        })


# =============================================================================
# ConsortiumMember (nested bajo /consortiums/{id}/members/)
# =============================================================================


class ConsortiumMemberViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Gestión de miembros de un consorcio.

    - list:  listar miembros del consorcio.
    - join:  la empresa del usuario solicita unirse (action POST).
    - leave: la empresa del usuario abandona el consorcio (action POST).
    """

    serializer_class = ConsortiumMemberSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def _get_consortium(self):
        """Obtiene el consorcio desde la URL y verifica que exista."""
        return get_object_or_404(Consortium, pk=self.kwargs["consortium_pk"])

    def get_queryset(self):
        """Miembros del consorcio especificado, filtrados por visibilidad."""
        consortium = self._get_consortium()
        user = self.request.user

        if not user.company:
            return ConsortiumMember.objects.none()

        # Solo miembros activos del consorcio o el owner pueden ver la lista
        is_owner = consortium.owner_id == user.company_id
        is_member = ConsortiumMember.objects.filter(
            consortium=consortium,
            company=user.company,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()

        if is_owner or is_member:
            return ConsortiumMember.objects.filter(consortium=consortium)

        return ConsortiumMember.objects.none()

    @action(detail=False, methods=["post"])
    def join(self, request, consortium_pk=None):
        """
        La empresa del usuario solicita unirse al consorcio.

        Si el consorcio esta en estado draft o active, se crea un registro
        de miembro con status pending.
        """
        consortium = self._get_consortium()
        company = request.user.company

        if not company:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar que la empresa no sea ya miembro
        existing = ConsortiumMember.objects.filter(
            consortium=consortium,
            company=company,
        ).first()

        if existing:
            if existing.status == ConsortiumMember.Status.ACTIVE:
                return Response(
                    {"detail": "Tu empresa ya es miembro activo de este consorcio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if existing.status == ConsortiumMember.Status.PENDING:
                return Response(
                    {"detail": "Ya existe una solicitud pendiente para tu empresa."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Si fue rechazado, salio o removido, permitir reintento
            existing.status = ConsortiumMember.Status.PENDING
            existing.role = ConsortiumMember.Role.CONTRIBUTOR
            existing.save(update_fields=["status", "role", "updated_at"])
            serializer = ConsortiumMemberSerializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Crear nueva solicitud de membresía
        member = ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.PENDING,
        )

        serializer = ConsortiumMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def leave(self, request, consortium_pk=None):
        """
        La empresa del usuario abandona el consorcio.

        El owner no puede abandonar su propio consorcio.
        """
        consortium = self._get_consortium()
        company = request.user.company

        if not company:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # El owner no puede abandonar
        if consortium.owner_id == company.id:
            return Response(
                {"detail": "El propietario no puede abandonar su consorcio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member = ConsortiumMember.objects.filter(
            consortium=consortium,
            company=company,
            status=ConsortiumMember.Status.ACTIVE,
        ).first()

        if not member:
            return Response(
                {"detail": "Tu empresa no es miembro activo de este consorcio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.status = ConsortiumMember.Status.LEFT
        member.save(update_fields=["status", "updated_at"])

        return Response(
            {"detail": "Tu empresa ha abandonado el consorcio."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, consortium_pk=None, pk=None):
        """Approve a pending membership request (owner only)."""
        consortium = self._get_consortium()
        if consortium.owner_id != request.user.company_id:
            return Response(
                {"detail": "Solo el propietario puede aprobar miembros."},
                status=status.HTTP_403_FORBIDDEN,
            )
        member = get_object_or_404(
            ConsortiumMember, pk=pk, consortium=consortium
        )
        if member.status != ConsortiumMember.Status.PENDING:
            return Response(
                {"detail": "Solo se pueden aprobar solicitudes pendientes."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member.status = ConsortiumMember.Status.ACTIVE
        member.save(update_fields=["status", "updated_at"])
        return Response(ConsortiumMemberSerializer(member).data)

    @action(detail=True, methods=["post"])
    def remove(self, request, consortium_pk=None, pk=None):
        """Remove an active member from the consortium (owner only)."""
        consortium = self._get_consortium()
        if consortium.owner_id != request.user.company_id:
            return Response(
                {"detail": "Solo el propietario puede remover miembros."},
                status=status.HTTP_403_FORBIDDEN,
            )
        member = get_object_or_404(
            ConsortiumMember, pk=pk, consortium=consortium
        )
        if member.role == ConsortiumMember.Role.OWNER:
            return Response(
                {"detail": "No se puede remover al propietario."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member.status = ConsortiumMember.Status.REMOVED
        member.save(update_fields=["status", "updated_at"])
        return Response(ConsortiumMemberSerializer(member).data)


# =============================================================================
# ContributionProof (nested bajo /consortiums/{id}/contributions/)
# =============================================================================


class ContributionProofViewSet(
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    """
    Pruebas de contribución de un consorcio.

    - list:   solo lectura filtrado por empresa/consorcio.
    - create: permite a miembros activos enviar una nueva prueba de contribución.
    """

    serializer_class = ContributionProofSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def get_serializer_class(self):
        if self.action == "create":
            return ContributionProofCreateSerializer
        return ContributionProofSerializer

    def perform_create(self, serializer):
        consortium_pk = self.kwargs.get("consortium_pk")
        serializer.save(
            company=self.request.user.company,
            consortium_id=consortium_pk,
        )

    def get_queryset(self):
        consortium_pk = self.kwargs.get("consortium_pk")
        user = self.request.user

        if not user.company:
            return ContributionProof.objects.none()

        queryset = ContributionProof.objects.filter(consortium_id=consortium_pk)

        # El owner del consorcio puede ver todas las contribuciones
        try:
            consortium = Consortium.objects.get(pk=consortium_pk)
        except Consortium.DoesNotExist:
            return ContributionProof.objects.none()

        if consortium.owner_id == user.company_id:
            return queryset

        # Miembros solo ven sus propias contribuciones
        return queryset.filter(company=user.company)

    @action(detail=False, methods=["get"])
    def my_contributions(self, request, consortium_pk=None):
        """Return only the current company's contributions."""
        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        qs = ContributionProof.objects.filter(
            consortium_id=consortium_pk, company=user.company
        )
        return Response(ContributionProofSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def summary(self, request, consortium_pk=None):
        """Return aggregate stats about contributions in this consortium."""
        qs = self.get_queryset()
        total = qs.count()
        verified = qs.filter(verified=True).count()
        total_records = sum(c.record_count for c in qs)
        return Response(
            {
                "total_contributions": total,
                "verified_contributions": verified,
                "total_records": total_records,
            }
        )


# =============================================================================
# TrainingResult (nested bajo /consortiums/{id}/training-results/)
# =============================================================================


class TrainingResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista de solo lectura de resultados de entrenamiento de un consorcio.

    Todos los miembros activos pueden ver los resultados.
    """

    serializer_class = TrainingResultSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def get_queryset(self):
        consortium_pk = self.kwargs.get("consortium_pk")
        user = self.request.user

        if not user.company:
            return TrainingResult.objects.none()

        return TrainingResult.objects.filter(consortium_id=consortium_pk)


# =============================================================================
# ConsortiumInvitation
# =============================================================================


class ConsortiumInvitationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Gestión de invitaciones a consorcios.

    - list:    invitaciones enviadas por la empresa o recibidas por ella.
    - create:  enviar una invitacion (solo owner/admin del consorcio).
    - accept:  aceptar una invitacion (action POST).
    - reject:  rechazar una invitacion (action POST).
    """

    serializer_class = ConsortiumInvitationSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Muestra invitaciones enviadas o recibidas por la empresa del usuario."""
        user = self.request.user
        if not user.company:
            return ConsortiumInvitation.objects.none()

        company = user.company

        # Invitaciones enviadas por la empresa
        sent = ConsortiumInvitation.objects.filter(inviter=company)

        # Invitaciones recibidas (por empresa FK, por email del usuario, o por email de la empresa)
        received = ConsortiumInvitation.objects.filter(invitee_company=company)
        received_by_user_email = ConsortiumInvitation.objects.filter(
            invitee_email=user.email,
        )
        received_by_company_email = ConsortiumInvitation.objects.filter(
            invitee_email=company.email,
        )

        return (sent | received | received_by_user_email | received_by_company_email).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return ConsortiumInvitationCreateSerializer
        return ConsortiumInvitationSerializer

    def perform_create(self, serializer):
        """
        Crea la invitacion asignando la empresa del usuario como inviter.

        Solo el owner o admin del consorcio puede enviar invitaciones.
        """
        from rest_framework.exceptions import PermissionDenied

        company = self.request.user.company
        consortium = serializer.validated_data["consortium"]

        # Verificar que la empresa es owner o admin del consorcio
        is_owner = consortium.owner_id == company.id
        is_admin = ConsortiumMember.objects.filter(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.ADMIN,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()

        if not is_owner and not is_admin:
            raise PermissionDenied(
                "Solo el propietario o un admin del consorcio puede enviar invitaciones."
            )

        # Resolver la empresa invitada si existe un usuario con ese email
        from apps.core.models import User
        invitee_email = serializer.validated_data["invitee_email"]
        invitee_company = None
        try:
            invitee_user = User.objects.get(email=invitee_email)
            invitee_company = invitee_user.company
        except User.DoesNotExist:
            pass

        # Valor por defecto para expires_at si no fue proporcionado
        expires_at = serializer.validated_data.get("expires_at")
        if not expires_at:
            from datetime import timedelta
            expires_at = timezone.now() + timedelta(days=30)

        serializer.save(
            inviter=company,
            invitee_company=invitee_company,
            expires_at=expires_at,
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        Acepta una invitacion pendiente.

        Crea el registro de miembro con status activo y el rol indicado
        en la invitacion.
        """
        invitation = self.get_object()
        company = request.user.company

        if not company:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar que la invitacion es para esta empresa o para el email del usuario
        if (
            invitation.invitee_company_id
            and invitation.invitee_company_id != company.id
        ):
            return Response(
                {"detail": "Esta invitacion no es para tu empresa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            not invitation.invitee_company_id
            and invitation.invitee_email != request.user.email
            and invitation.invitee_email != company.email
        ):
            return Response(
                {"detail": "Esta invitacion no es para ti."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != ConsortiumInvitation.Status.PENDING:
            return Response(
                {"detail": f"La invitacion ya fue {invitation.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.is_expired:
            invitation.status = ConsortiumInvitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            return Response(
                {"detail": "La invitacion ha expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Aceptar la invitacion
        invitation.status = ConsortiumInvitation.Status.ACCEPTED
        invitation.responded_at = timezone.now()
        invitation.invitee_company = company
        invitation.save(update_fields=["status", "responded_at", "invitee_company"])

        # Crear o reactivar miembro
        member, created = ConsortiumMember.objects.get_or_create(
            consortium=invitation.consortium,
            company=company,
            defaults={
                "role": invitation.role,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        if not created:
            member.role = invitation.role
            member.status = ConsortiumMember.Status.ACTIVE
            member.save(update_fields=["role", "status", "updated_at"])

        serializer = ConsortiumInvitationSerializer(invitation)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """
        Rechaza una invitacion pendiente.
        """
        invitation = self.get_object()
        company = request.user.company

        if not company:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar que la invitacion es para esta empresa o para el email del usuario
        if (
            invitation.invitee_company_id
            and invitation.invitee_company_id != company.id
        ):
            return Response(
                {"detail": "Esta invitacion no es para tu empresa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            not invitation.invitee_company_id
            and invitation.invitee_email != request.user.email
            and invitation.invitee_email != company.email
        ):
            return Response(
                {"detail": "Esta invitacion no es para ti."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != ConsortiumInvitation.Status.PENDING:
            return Response(
                {"detail": f"La invitacion ya fue {invitation.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation.status = ConsortiumInvitation.Status.DECLINED
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at"])

        serializer = ConsortiumInvitationSerializer(invitation)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        """Alias for reject — decline a pending invitation."""
        return self.reject(request, pk=pk)

    @action(detail=False, methods=["get"])
    def received(self, request):
        """List invitations received by the current company."""
        company = request.user.company
        if not company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        invitations = ConsortiumInvitation.objects.filter(
            invitee_company=company
        ) | ConsortiumInvitation.objects.filter(invitee_email=request.user.email)
        invitations = invitations.distinct()
        return Response(ConsortiumInvitationSerializer(invitations, many=True).data)

    @action(detail=False, methods=["get"])
    def sent(self, request):
        """List invitations sent by the current company."""
        company = request.user.company
        if not company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        invitations = ConsortiumInvitation.objects.filter(inviter=company)
        return Response(ConsortiumInvitationSerializer(invitations, many=True).data)
