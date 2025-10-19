# experiences/serializers.py

from rest_framework import serializers
from .models import Experience, Booking
from nsocial.serializers import CurrentUserSerializer # Reutilizamos este serializer

class ExperienceSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y listar experiencias.
    """
    host = CurrentUserSerializer(read_only=True)

    class Meta:
        model = Experience
        fields = [
            'id', 'host', 'title', 'city', 'date', 'duration_in_minutes',
            'max_guests', 'cost', 'photo', 'stripe_product_id', 'created_at'
        ]
        read_only_fields = ['id', 'host', 'created_at']

class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer para las reservaciones. Muestra detalles de la experiencia y del invitado.
    """
    experience = ExperienceSerializer(read_only=True)
    guest = CurrentUserSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'experience', 'guest', 'status', 'created_at']

