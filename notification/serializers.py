from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'actor', 'actor_name', 'verb', 'description',
            'target_content_type', 'target_object_id', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'recipient', 'actor_name', 'created_at']

    def get_actor_name(self, obj):
        if obj.actor:
            return getattr(obj.actor, 'get_full_name', lambda: str(obj.actor))()
        return None
