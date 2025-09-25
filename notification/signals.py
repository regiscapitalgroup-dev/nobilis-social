import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .serializers import NotificationSerializer


@receiver(post_save, sender=Notification)
def notify_ws_on_create(sender, instance: Notification, created: bool, **kwargs):
    if not created:
        return
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    group_name = f'user_{instance.recipient_id}_notifications'
    payload = NotificationSerializer(instance).data
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notify',
            'payload': payload
        }
    )
