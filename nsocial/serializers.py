from rest_framework import serializers
from nsocial.models import CustomUser, UserProfile, SocialMediaProfile
from api.models import LanguageCatalog
import json
from django.contrib.auth.password_validation import validate_password

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    class Meta:
        model = CustomUser
        fields = ['email', 'password']
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            validated_data['email'],
            validated_data['password']
        )
        return user


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields =('first_name', 'last_name', 'email', 'id')


class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    refresh_token = serializers.CharField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class TokenSerializer(serializers.Serializer):
    token = serializers.TimeField(required=True)


class SocialMediaProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = SocialMediaProfile
        fields = ['id', 'platform_name', 'profile_url']


class JsonStringArrayField(serializers.ListField):
    """
    Campo que espera un string JSON con un array
    y lo convierte en una lista de Python.
    Ahora también maneja datos que ya llegan como una lista.
    """

    def to_internal_value(self, data):
        # Si los datos ya son una lista, simplemente úsalos.
        if isinstance(data, list):
            return super().to_internal_value(data)

        # Si los datos son un string, intenta decodificarlo como JSON.
        if isinstance(data, str):
            try:
                # Esto manejará un string como '["Spanish", "English"]'
                return json.loads(data)
            except (TypeError, ValueError):
                # Esto manejará un string como 'Spanish' (un solo valor)
                return [data]

        # Si no es ni lista ni string, falla.
        self.fail('invalid', format='json')


class UserProfileSerializer(serializers.ModelSerializer):
    languages = serializers.StringRelatedField(many=True, read_only=True)

    # 2. CAMPO DE SOLO ESCRITURA: Para recibir y procesar la entrada.
    #    Usamos nuestro campo personalizado y lo marcamos como 'write_only'.
    #    Le damos un nombre distinto para evitar conflictos.
    languages_input = JsonStringArrayField(
        child=serializers.SlugRelatedField(
            queryset=LanguageCatalog.objects.all(),
            slug_field='name'
        ),
        required=False,
        write_only=True,
        source='languages'  # También apunta a la relación 'languages'
    )
    social_media_profiles = SocialMediaProfileSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'introduction_headline',
            'alias_title',
            'profile_picture',
            'birthday',
            'phone_number',
            'street',
            'city',
            'postal_code',
            'languages',
            'languages_input',
            'social_media_profiles',
        ]


class PasswordResetConfirmSerializer(serializers.Serializer):
    user = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password], 
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        return attrs
