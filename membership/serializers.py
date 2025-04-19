from rest_framework import serializers
from membership.models import Plan, Subscription
import datetime


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'stripe_plan_id', 'title', 'price', 'interval']
        read_only_fields = ['id', 'stripe_plan_id', 'title', 'price', 'interval'] # Estos se definen en Stripe


class SubscriptionCreateSerializer(serializers.Serializer):
    price_id = serializers.CharField(max_length=100, required=True)
    payment_method_id = serializers.CharField(max_length=100, required=True) # Token o ID del método de pago de Stripe


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'status', 'start_date', 'end_date']
        read_only_fields = ['id', 'status', 'start_date', 'end_date', 'plan']


class ProductSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    # Puedes añadir más campos del producto si los necesitas (images, metadata, etc.)

class RecurringPriceSerializer(serializers.Serializer):
    interval = serializers.CharField()
    interval_count = serializers.IntegerField()
    # trial_period_days = serializers.IntegerField(allow_null=True) # Si aplica

class PriceSerializer(serializers.Serializer):
    id = serializers.CharField() # El ID del Precio (price_xxx...) ¡Importante para la suscripción!
    unit_amount = serializers.IntegerField() # Precio en la unidad mínima (ej: centavos)
    currency = serializers.CharField()
    recurring = RecurringPriceSerializer()
    product = ProductSerializer() # Anida la información del producto
    # Puedes añadir 'metadata' si usas metadatos en tus precios        

class PaymentMethodCardSerializer(serializers.Serializer):
    brand = serializers.CharField()
    last4 = serializers.CharField()

class DefaultPaymentMethodSerializer(serializers.Serializer):
    # Nota: El objeto payment method expandido puede tener diferentes estructuras
    # Aquí asumimos que es una tarjeta (card)
    card = PaymentMethodCardSerializer(allow_null=True)
    # Podrías necesitar manejar otros tipos como 'sepa_debit', etc. si los usas

class SubscriptionStatusSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    current_period_start = serializers.DateTimeField()
    current_period_end = serializers.DateTimeField()
    cancel_at_period_end = serializers.BooleanField()
    canceled_at = serializers.DateTimeField(allow_null=True)
    trial_end = serializers.DateTimeField(allow_null=True)
    # Anida la información del plan (Precio y Producto)
    plan = PriceSerializer() # Reutiliza el serializer de Precio que ya incluye Producto
    # Información básica del método de pago por defecto
    default_payment_method = DefaultPaymentMethodSerializer(allow_null=True, required=False) # Si lo expandiste

    # Convertir timestamps de Stripe (segundos desde epoch) a DateTime de Python/DRF
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field_name in ['current_period_start', 'current_period_end', 'canceled_at', 'trial_end']:
            if representation.get(field_name):
                timestamp = instance.get(field_name)
                if timestamp:
                    representation[field_name] = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                else:
                     representation[field_name] = None # Asegurar que nulos se manejen bien
            # Si el campo no está presente en los datos de entrada (Stripe), DRF lo omitirá o dará error
            # a menos que manejes su ausencia explícitamente o uses default/allow_null.
            # Aquí asumimos que los campos relevantes estarán presentes si son aplicables.

        # Asegurar que default_payment_method no cause error si no se expandió o es null
        if 'default_payment_method' not in instance or instance['default_payment_method'] is None:
            representation.pop('default_payment_method', None)

        return representation