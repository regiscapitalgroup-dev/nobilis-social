"""
ASGI config for nobilis project with Django Channels.
"""
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nobilis.settings')

# Standard Django ASGI application
http_application = get_asgi_application()

# Import websocket routes lazily to avoid AppRegistryNotReady
def get_websocket_urlpatterns():
    from notification.routing import websocket_urlpatterns as notif_ws
    return notif_ws

application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": AuthMiddlewareStack(
        URLRouter(get_websocket_urlpatterns())
    ),
})
