from rest_framework import serializers
from membership.models import MembershipPlan, Suscription


class MembershipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = '__all__'


class SuscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suscription
        fields = '__all__'
