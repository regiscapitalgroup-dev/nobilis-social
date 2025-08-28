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


class UserProfileSerializer(serializers.ModelSerializer):
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
