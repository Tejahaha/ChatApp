from django.urls import re_path
from chat import consumers
from notifications import consumers as notif_consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/group/(?P<group_id>\d+)/$', consumers.GroupChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', notif_consumers.NotificationConsumer.as_asgi()),
]
