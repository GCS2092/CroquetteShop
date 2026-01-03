import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import Order, Conversation, Message, Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()

class OrderChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.group_name = f"order_{self.order_id}"

        user = self.scope['user']
        # Only authenticated users can join (further permission checks below)
        if not user.is_authenticated:
            await self.close()
            return

        # Basic permission: user is either the order owner (user) or staff (admin)
        allowed = await self._user_can_access_order(user, self.order_id)
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message_text = data.get('message')
        user = self.scope['user']

        if not message_text:
            return

        # Save message to DB
        message_obj = await self._create_message(user, int(self.order_id), message_text)

        # Broadcast to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.message',
                'message': message_text,
                'sender': user.username,
                'created_at': message_obj.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def _user_can_access_order(self, user, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return False
        # Owner can access
        if order.user and order.user == user:
            return True
        # Staff (admin) can access
        if user.is_staff:
            return True
        return False

    @database_sync_to_async
    def _create_message(self, user, order_id, content):
        order = Order.objects.get(id=order_id)
        # Ensure a conversation exists
        conv, _ = Conversation.objects.get_or_create(order=order)
        # Ensure participants include sender and owner/admin
        if order.user:
            conv.participants.add(order.user)
        if order.assigned_to:
            conv.participants.add(order.assigned_to)
        conv.participants.add(user)
        msg = Message.objects.create(conversation=conv, sender=user, content=content)

        # Create notifications for other participants
        for participant in conv.participants.exclude(pk=user.pk).all():
            try:
                Notification.objects.create(
                    recipient=participant,
                    verb=f"Nouveau message sur la commande #{order.id}",
                    url=f"/commande/{order.id}/chat/"
                )
            except Exception:
                # Be resilient in case notifications cannot be created in some test environments
                pass

        return msg


class NotificationsConsumer(AsyncWebsocketConsumer):
    """Gère les notifications en temps réel pour l'utilisateur connecté."""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # For now, client doesn't send messages here.
        pass

    async def notify(self, event):
        # event.payload contains notification data
        await self.send(text_data=json.dumps(event.get('payload', {})))
