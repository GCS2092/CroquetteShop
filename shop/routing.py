from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # Ex: ws://.../ws/orders/123/
    re_path(r"ws/orders/(?P<order_id>[^/]+)/$", consumers.OrderChatConsumer.as_asgi()),
    # Notifications for authenticated users: ws://.../ws/notifications/
    re_path(r"ws/notifications/$", consumers.NotificationsConsumer.as_asgi()),
]
