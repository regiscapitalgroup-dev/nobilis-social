from rest_framework import serializers
from membership.models import Plan, ShippingAddress
import datetime
import logging # Para logs en to_representation si es necesario
import stripe

logger = logging.getLogger(__name__)


class PaymentMethodSetupSerializer(serializers.Serializer):
    """ Valida el ID del método de pago para la configuración inicial. """
    payment_method_id = serializers.CharField(max_length=100, required=True)

class SubscriptionCreateSerializer(serializers.Serializer):
    """ Valida el ID del precio para crear la suscripción (asume que el pago ya está configurado). """
    price_id = serializers.CharField(max_length=100, required=True) # Solo necesita price_id


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'stripe_plan_id', 'title', 'price', 'interval']
        read_only_fields = ['id', 'stripe_plan_id', 'title', 'price', 'interval'] # Estos se definen en Stripe


class SubscriptionCreateSerializer(serializers.Serializer):
    price_id = serializers.CharField(max_length=100, required=True)
    payment_method_id = serializers.CharField(max_length=100, required=True) # Token o ID del método de pago de Stripe


class ProductSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    # Puedes añadir más campos del producto si los necesitas (images, metadata, etc.)

class RecurringPriceSerializer(serializers.Serializer):
    interval = serializers.CharField(required=False, allow_null=True)
    interval_count = serializers.IntegerField(required=False, allow_null=True)
    # trial_period_days = serializers.IntegerField(allow_null=True) # Si aplica

class PriceSerializer(serializers.Serializer):
    id = serializers.CharField() # El ID del Precio (price_xxx...) ¡Importante para la suscripción!
    unit_amount = serializers.IntegerField(required=False, allow_null=True) # Precio en la unidad mínima (ej: centavos)
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
    # Hacer los campos de fecha opcionales para evitar KeyErrors iniciales
    current_period_start = serializers.DateTimeField(required=False, allow_null=True)
    current_period_end = serializers.DateTimeField(required=False, allow_null=True)
    cancel_at_period_end = serializers.BooleanField(required=False, allow_null=True, default=False)
    canceled_at = serializers.DateTimeField(allow_null=True, required=False)
    trial_end = serializers.DateTimeField(allow_null=True, required=False)

    # ---> USA PlanSerializer en lugar de PriceSerializer <---
    plan = PlanSerializer(required=False, allow_null=True)

    default_payment_method = DefaultPaymentMethodSerializer(allow_null=True, required=False)

    def to_representation(self, instance):
        """ Convierte el objeto Subscription de Stripe a un diccionario serializable. """
        # Usar getattr para acceso seguro a todos los atributos de la instancia de Stripe
        representation = {
            'id': getattr(instance, 'id', None),
            'status': getattr(instance, 'status', None),
            'cancel_at_period_end': getattr(instance, 'cancel_at_period_end', False),
            'canceled_at': None, # Inicializar fechas
            'current_period_start': None,
            'current_period_end': None,
            'trial_end': None,
            'plan': None, # Inicializar objetos anidados
            'default_payment_method': None
        }

        # Convertir timestamps de forma segura
        for field_name in ['canceled_at', 'current_period_start', 'current_period_end', 'trial_end']:
            timestamp = getattr(instance, field_name, None)
            if timestamp:
                try:
                    representation[field_name] = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                except (TypeError, ValueError):
                    representation[field_name] = None # Mantener None si hay error de conversión

        # Serializar Plan de forma segura
        plan_obj = getattr(instance, 'plan', None)
        if plan_obj:
            # Opcional: Si necesitas el objeto Product completo, asegúrate de expandirlo
            # en la llamada retrieve ('plan.product') y ajusta PlanSerializer/ProductSerializer
            try:
                # Si el plan tiene el objeto producto embebido (por expand)
                if isinstance(getattr(plan_obj,'product', None), stripe.Product):
                     # Necesitaríamos ProductSerializer definido y PlanSerializer que lo use
                     # Ajuste PlanSerializer: product = ProductSerializer(required=False, allow_null=True)
                     representation['plan'] = PlanSerializer(plan_obj).data
                # Si el plan solo tiene el ID del producto como string
                elif isinstance(getattr(plan_obj,'product', None), str):
                     # Usar un PlanSerializer que solo espera el ID del producto
                     # Ajuste PlanSerializer: product = serializers.CharField()
                     representation['plan'] = PlanSerializer(plan_obj).data
                else: # Si no hay info del producto o es inesperada
                     representation['plan'] = PlanSerializer(plan_obj).data # Intentar serializar sin producto detallado
            except Exception as e:
                 logger.error(f"Error serializando Plan {getattr(plan_obj, 'id', 'N/A')}: {e}")
                 representation['plan'] = {'id': getattr(plan_obj, 'id', None), 'error': 'Could not serialize plan details'}


        # Serializar Default Payment Method de forma segura
        pm_obj = getattr(instance, 'default_payment_method', None)
        if pm_obj:
            try:
                 representation['default_payment_method'] = DefaultPaymentMethodSerializer(pm_obj).data
            except Exception as e:
                 logger.error(f"Error serializando Default PM {getattr(pm_obj, 'id', 'N/A')}: {e}")
                 representation['default_payment_method'] = {'id': getattr(pm_obj, 'id', None), 'error': 'Could not serialize payment details'}


        return representation
    

class PlanNobilisSerializer(serializers.ModelSerializer):
    price = serializers.FloatField()

    class Meta:
        model = Plan
        fields = '__all__'


class PlanNobilisPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        # Aquí especificamos la lista de campos que queremos mostrar
        fields = ['id', 'title', 'price_year', 'price_str']


class PlanSerializer(serializers.Serializer):
    """ Serializa un objeto Plan (legacy) de Stripe. """
    id = serializers.CharField()
    amount = serializers.IntegerField() # Los Planes usan 'amount'
    currency = serializers.CharField()
    interval = serializers.CharField() # 'interval' está directamente en el Plan
    interval_count = serializers.IntegerField() # 'interval_count' está directamente en el Plan
    # El 'product' en un Plan es solo el ID del producto.
    # Podemos devolver solo el ID o intentar serializar el objeto Product si lo expandimos.
    product = serializers.CharField() # Devuelve el ID del producto asociado al plan


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'user', 'name', 'address', 'country', 'city', 'card_no',
            'card_type', 'card_last_4', 'same_billing_address',
            'billing_address'
        ]

        # --- 2. AÑADE ESTA SECCIÓN ---
        extra_kwargs = {
            'id': {'read_only': True},
            'user': {'read_only': True},
            'card_no': {'write_only': True}
        }
