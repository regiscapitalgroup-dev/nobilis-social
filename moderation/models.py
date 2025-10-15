# moderation/models.py

from django.db import models
from django.conf import settings
import uuid
from nsocial.models import Role

class Team(models.Model):
    """
    Representa un equipo de moderación.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre del Equipo')
    description = models.TextField(blank=True, default='', verbose_name='Descripción')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Moderation Team'
        verbose_name_plural = 'Moderations Teams'
        ordering = ['name']


class TeamMembership(models.Model):
    """
    Define la membresía de un usuario en un equipo, incluyendo su rol.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='team_memberships', verbose_name='Rol')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Ingreso')

    def __str__(self):
        return f'{self.user.email} en {self.team.name} como {self.role.name}'

    class Meta:
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'
        # Un usuario no puede pertenecer dos veces al mismo equipo
        unique_together = ('user', 'team')
        ordering = ['team', 'user']


class ModeratorInvitation(models.Model):
    """
    Gestiona los tokens de invitación temporales exclusivos para
    colaboradores y moderadores.
    """
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_moderator_invitations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitación para {self.email}"


class ModeratorProfile(models.Model):
    """
    Almacena información adicional y específica para los colaboradores
    invitados que no tienen suscripción.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moderator_profile'
    )
    organization = models.CharField(max_length=255, blank=True, null=True, verbose_name='Organización')
    relation = models.CharField(max_length=255, blank=True, null=True, verbose_name='Relación')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de Colaborador para {self.user.email}"

    class Meta:
        verbose_name = 'Perfil de Colaborador'
        verbose_name_plural = 'Perfiles de Colaboradores'
