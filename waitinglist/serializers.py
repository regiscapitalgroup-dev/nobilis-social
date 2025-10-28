from rest_framework import serializers
from waitinglist.models import WaitingList, RejectionReason
import datetime
from django.utils import timezone
from django.conf import settings


class WaitingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitingList
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'status']


class RejectWaitingListSerializer(serializers.Serializer):
    rejection_reason_id = serializers.PrimaryKeyRelatedField(
        queryset=RejectionReason.objects.all(),
        allow_null=False,
        required=True,
        source='rejection_reason',
        help_text="ID del motivo de rechazo del catálogo RejectionReason."
    )
    notes = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Notas adicionales."
    )


class ExistingUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_null=False)


class SafeDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            value = datetime.datetime.combine(value, datetime.time.min)
            if settings.USE_TZ:
                value = timezone.make_aware(value)
        elif isinstance(value, datetime.datetime) and settings.USE_TZ and timezone.is_naive(value):
            value = timezone.make_aware(value)

        return super().to_representation(value)


class WaitingListAdminListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    requested = SafeDateTimeField(source='created_at', read_only=True) # Renombramos date_joined
    category = serializers.SerializerMethodField()
    assigned = serializers.SerializerMethodField()

    class Meta:
        model = WaitingList
        fields = [
            'id',
            'full_name',
            'source',
            'country',
            'requested',
            'category',
            'assigned',
            'status',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() #

    def get_source(self, obj):
        return "Waiting List"

    def get_country(self, obj):
        # Intenta extraer el país del campo city (asumiendo formato "Ciudad, País")
        if obj.city and ',' in obj.city: #
            parts = obj.city.split(',')
            # Toma la última parte y quita espacios en blanco
            country = parts[-1].strip()
            return country
        # Si no tiene el formato esperado o está vacío, devuelve null o una cadena vacía
        return None

    def get_category(self, obj):
        # Valor fijo según lo solicitado
        return "Category"

    def get_assigned(self, obj):
        # Obtiene el nombre del usuario admin que está haciendo la petición
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            # Puedes elegir qué mostrar: email, nombre completo, etc.
            return f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
        return "N/A" # O algún valor por defecto si no hay usuario


class RejectionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RejectionReason
        fields = ['id', 'reason']

