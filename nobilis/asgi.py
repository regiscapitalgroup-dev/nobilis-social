import os
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nobilis.settings')


http_application = get_asgi_application()


from channels.routing import ProtocolTypeRouter, URLRouter
from notification.middleware import JwtAuthMiddleware
import notification.routing


application = ProtocolTypeRouter({
  "http": http_application,
  "websocket": JwtAuthMiddleware(
        URLRouter(
            notification.routing.websocket_urlpatterns
        )
    ),
})