from rest_framework import serializers
from .models import CustomUser


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
