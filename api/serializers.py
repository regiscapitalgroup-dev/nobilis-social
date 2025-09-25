from rest_framework import serializers
from .models import CityCatalog, LanguageCatalog, Relative, RelationshipCatalog, SupportAgent


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


class RelationshipCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationshipCatalog
        fields = ['id', 'name', 'description',]
        read_only_fields = ['id', ]


class RelativeSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    # Show relationship name (text) in responses
    relationship = serializers.StringRelatedField(read_only=True)
    # Accept relationship by ID in requests
    relationship_id = serializers.PrimaryKeyRelatedField(source='relationship', queryset=RelationshipCatalog.objects.all(), write_only=True)

    class Meta:
        model = Relative
        fields = ['id', 'user', 'first_name', 'last_name', 'year_of_birth', 'relationship', 'relationship_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'relationship']


class SupportAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportAgent
        fields = ['id', 'name', 'email', 'phone_number', 'aviable_until']
        read_only_fields = ['id']
