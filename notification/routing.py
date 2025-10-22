from django.urls import re_path
from .consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"api/v1/ws/notifications/$", NotificationConsumer.as_asgi()),
]
