from rest_framework import serializers
from waitinglist.models import WaitingList, Category, Motivation
from django.contrib.auth.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class MotivationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motivation
        fields = '__all__'


class WaitingListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    motivations = MotivationSerializer(many=True, read_only=True)
    class Meta:
        model = WaitingList
        fields = '__all__'

