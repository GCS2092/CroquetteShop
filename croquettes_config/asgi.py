"""
ASGI config for croquettes_config project (Channels-enabled).

This file configures a ProtocolTypeRouter with HTTP and WebSocket support.
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'croquettes_config.settings')
django.setup()

from django.core.asgi import get_asgi_application

# Import websocket routes from the shop app
from shop import routing as shop_routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            shop_routing.websocket_urlpatterns
        )
    ),
})
