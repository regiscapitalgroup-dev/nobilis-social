from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Team, TeamMembership
from .serializers import TeamSerializer, TeamMembershipSerializer


class IsAdminRole(permissions.BasePermission):
    """
    Permiso personalizado para permitir el acceso solo a usuarios con el flag 'is_admin'.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'is_admin', False)


class TeamMembershipViewSet(viewsets.ModelViewSet):
    """
    ViewSet para añadir, ver y eliminar miembros de un equipo específico.
    Solo accesible por administradores.
    """
    serializer_class = TeamMembershipSerializer
    permission_classes = [IsAdminRole]

    def get_team_object(self):
        """Obtiene el objeto del equipo desde el URL parameter."""
        team_pk = self.kwargs.get('team_pk')
        return get_object_or_404(Team, pk=team_pk)

    def get_queryset(self):
        """Filtra los miembros para que pertenezcan solo al equipo especificado."""
        team = self.get_team_object()
        return TeamMembership.objects.filter(team=team).select_related('user', 'role')

    def perform_create(self, serializer):
        """Asocia automáticamente el nuevo miembro con el equipo de la URL."""
        team = self.get_team_object()
        serializer.save(team=team)

    def get_serializer_context(self):
        """Pasa la vista al contexto del serializer para validaciones."""
        context = super().get_serializer_context()
        context['view'] = self
        return context


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar equipos de moderación.
    La consulta ha sido optimizada para incluir todos los datos de los miembros.
    """
    # --- QUERYSET MODIFICADO Y OPTIMIZADO ---
    queryset = Team.objects.prefetch_related(
        'members__user__profile',  # Carga el UserProfile de cada usuario
        'members__user__moderator_profile',  # Carga el ModeratorProfile de cada usuario
        'members__role'  # Carga el Rol de cada miembro
    ).all()

    serializer_class = TeamSerializer
    permission_classes = [IsAdminRole]
