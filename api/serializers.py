from rest_framework import serializers
from waitinglist.models import WaitingList
from django.contrib.auth.models import User


class WaitingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitingList
        fields = '__all__'
