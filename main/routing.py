from django.urls import re_path,path
from main.apps.topic_mgt.actors.Broker import Broker

websocket_urlpatterns = [
    # re_path(r"^ws/conversation/(?P<conversation_uid>[^/]+)$", Prosumer.as_asgi()),
    # path("ws/test/", Prosumer.as_asgi()),
    re_path(r"^ws/conversation/(?P<conversation_uid>[^/]+)$", Broker.as_asgi()),
    path("ws/test/", Broker.as_asgi()),
]