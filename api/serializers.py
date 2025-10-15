from rest_framework import serializers
from .models import CityCatalog, LanguageCatalog, Relative, RelationshipCatalog, SupportAgent, IndustryCatalog, ProfessionalInterestCatalog, HobbyCatalog, ClubCatalog
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from nsocial.models import UserProfile, CustomUser, Role


class CityListSerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        parts = [instance.name]

        if instance.subcountry:
            parts.append(instance.subcountry)

        parts.append(instance.country)

        return ", ".join(parts)


class LanguageSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Language.
    """
    class Meta:
        model = LanguageCatalog
        fields = ['id', 'name'] # Devolvemos el ID y el nombre


class RelationshipCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationshipCatalog
        fields = ['id', 'name', 'description',]
        read_only_fields = ['id', ]


class RelativeSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    # Show relationship name (text) in responses
    relationship = serializers.StringRelatedField(read_only=True)
    # Accept relationship by ID in requests
    relationship_id = serializers.PrimaryKeyRelatedField(source='relationship', queryset=RelationshipCatalog.objects.all(), write_only=True)

    class Meta:
        model = Relative
        fields = ['id', 'user', 'first_name', 'last_name', 'year_of_birth', 'relationship', 'relationship_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'relationship']


class SupportAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportAgent
        fields = ['id', 'name', 'email', 'phone_number', 'aviable_until']
        read_only_fields = ['id']


class IndustryCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryCatalog
        fields = ['name']
        #read_only_fields = ['id']


class ProfessionalInterestCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalInterestCatalog
        fields = ['id', 'name', 'active']
        read_only_fields = ['id']


class HobbyCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HobbyCatalog
        fields = ['id', 'name', 'active']
        read_only_fields = ['id']


class ClubCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubCatalog
        fields = ['id', 'name', 'city', 'active']
        read_only_fields = ['id']


class ProfileIndustriesUpdateSerializer(serializers.Serializer):
    industry_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class ProfileInterestsUpdateSerializer(serializers.Serializer):
    interest_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class ProfileHobbiesUpdateSerializer(serializers.Serializer):
    hobby_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class TokenWithSubscriptionSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # Get cached subscription details from the user's profile (if exists)
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.stripe_subscription_id:
                data['subscription'] = {
                    'id': profile.stripe_subscription_id,
                    'status': profile.subscription_status,
                    'current_period_end': profile.subscription_current_period_end,
                    'cancel_at_period_end': profile.cancel_at_period_end,
                    'card': (
                        {'brand': profile.card_brand, 'last4': profile.card_last4}
                        if profile.card_last4 else None
                    )
                }
            else:
                data['subscription'] = None
        except UserProfile.DoesNotExist:
            data['subscription'] = None
        return data


class InviteUserSerializer(serializers.Serializer):
    """
    Serializer para validar los datos al invitar a un nuevo usuario.
    """
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)

    role_code = serializers.SlugRelatedField(
        queryset=Role.objects.all(),
        slug_field='code',  # Campo en el modelo Role usado para la búsqueda.
        source='role',  # La clave en `validated_data` será 'role'.
        required=True,
        help_text="Código del rol a asignar (ej. 'moderator')."
    )

    organization = serializers.CharField(max_length=255, required=False, allow_blank=True)
    relation = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_email(self, value):
        """
        Comprueba que no exista ya un usuario con el mismo correo electrónico.
        """
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un usuario con este correo electrónico ya existe.")
        return value
