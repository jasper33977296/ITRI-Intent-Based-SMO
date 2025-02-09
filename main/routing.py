from django.urls import re_path,path
from main.apps.workflow_mgt.actors.Prosumer import Prosumer

websocket_urlpatterns = [
    re_path(r"^ws/conversation/(?P<conversation_uid>[^/]+)$", Prosumer.as_asgi()),
    path("ws/test/", Prosumer.as_asgi()),
]