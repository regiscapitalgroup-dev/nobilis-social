from rest_framework import serializers
from membership.models import Plan, Subscription
import stripe
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'stripe_plan_id', 'title', 'price', 'interval']
        read_only_fields = ['id', 'stripe_plan_id', 'title', 'price', 'interval'] # Estos se definen en Stripe


class CreateSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(write_only=True)
    payment_method_id = serializers.CharField(max_length=255, write_only=True) # Token o ID del método de pago de Stripe


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'status', 'start_date', 'end_date']
        read_only_fields = ['id', 'status', 'start_date', 'end_date', 'plan']
