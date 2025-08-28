from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import ShippingAddress

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_shipping_address(sender, instance, created, **kwargs):
    if created:
        ShippingAddress.objects.create(user=instance)
