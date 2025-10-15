from rest_framework import serializers
from nsocial.models import CustomUser, Role
from nsocial.serializers import RoleSerializer
from .models import Team, TeamMembership


class TeamUserSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para mostrar información del usuario en un equipo.
    """

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name']


class TeamMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer para gestionar y mostrar los miembros de un equipo.
    """
    user = TeamUserSerializer(read_only=True)
    role = RoleSerializer(read_only=True)

    # Campos para la creación de una nueva membresía
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='user', write_only=True
    )
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source='role', write_only=True
    )

    class Meta:
        model = TeamMembership
        fields = ['id', 'user', 'role', 'user_id', 'role_id', 'joined_at']
        read_only_fields = ['id', 'joined_at']

    def validate(self, data):
        team = self.context['view'].get_team_object()
        if TeamMembership.objects.filter(team=team, user=data['user']).exists():
            raise serializers.ValidationError("Este usuario ya es miembro del equipo.")
        return data





class TeamMemberDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar la información detallada de un miembro
    de un equipo de moderación, combinando datos de múltiples modelos.
    """
    # Renombramos los campos y obtenemos datos de modelos relacionados usando 'source'
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    # Obtenemos el 'phone_number' del UserProfile del usuario
    phone_number = serializers.CharField(source='user.profile.phone_number', read_only=True, allow_null=True)

    # Obtenemos 'organization' y 'relation' del ModeratorProfile del usuario
    organization = serializers.CharField(source='user.moderator_profile.organization', read_only=True, allow_null=True)
    relation = serializers.CharField(source='user.moderator_profile.relation', read_only=True, allow_null=True)

    # Renombramos 'role.name' a 'assigment'
    assigment = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = TeamMembership
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'relation',
            'organization',
            'is_active',
            'assigment'
        ]


class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer para la gestión completa de un equipo, incluyendo sus miembros.
    """
    members = TeamMemberDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_at', 'members']
        read_only_fields = ['id', 'created_at']
