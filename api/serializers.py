from rest_framework import serializers
from waitinglist.models import WaitingList


class WaitingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitingList
        fields = '__all__'


class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    refresh_token = serializers.CharField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class TokenSerializer(serializers.Serializer):
    token = serializers.TimeField(required=True)
