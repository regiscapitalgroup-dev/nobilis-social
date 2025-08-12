# en tu_app/serializers.py

from rest_framework import serializers
from .models import CityCatalog


class CityListSerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        parts = [instance.name]

        if instance.subcountry:
            parts.append(instance.subcountry)

        parts.append(instance.country)

        return ", ".join(parts)
