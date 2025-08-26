from rest_framework import serializers
from .models import CityCatalog, LanguageCatalog


class CityListSerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        parts = [instance.name]

        if instance.subcountry:
            parts.append(instance.subcountry)

        parts.append(instance.country)

        return ", ".join(parts)


class LanguageSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Language.
    """
    class Meta:
        model = LanguageCatalog
        fields = ['id', 'name'] # Devolvemos el ID y el nombre
