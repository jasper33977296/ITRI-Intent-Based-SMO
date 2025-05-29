"""
ASGI config for main project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.core.asgi import get_asgi_application
from main.routing import websocket_urlpatterns
from main.apps.workflow_mgt.actors.Consumer import Consumer


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

application = ProtocolTypeRouter({
    # HTTP 協定 → Django 原生
    "http": get_asgi_application(),
    # WebSocket 協定 → 交給 Channels 路由
    "websocket": URLRouter(websocket_urlpatterns),
    "channel": ChannelNameRouter({
        "consumer": Consumer.as_asgi(),
    }),
})
