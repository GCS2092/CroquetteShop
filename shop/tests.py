from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from .models import Order, DeliveryLocation, Notification, Message

User = get_user_model()

class NotificationsTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user('alice', 'alice@example.com', 'pass')
        self.admin = User.objects.create_user('bob', 'bob@example.com', 'pass', is_staff=True)
        self.loc = DeliveryLocation.objects.create(name='Test')

    def test_notification_created_on_order(self):
        order = Order.objects.create(user=self.client_user, delivery_location=self.loc, total_amount=500, status='pending')
        # Notifications should be created for staff and user
        admin_notifications = Notification.objects.filter(recipient=self.admin, verb__icontains=f"Nouvelle commande #{order.id}")
        self.assertTrue(admin_notifications.exists())
        user_notifications = Notification.objects.filter(recipient=self.client_user, verb__icontains=f"Votre commande #{order.id}")
        self.assertTrue(user_notifications.exists())

class AdminPagesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass', is_staff=True)
        self.user = User.objects.create_user('u', 'u@example.com', 'pass')
        self.loc = DeliveryLocation.objects.create(name='Local')
        self.order1 = Order.objects.create(user=self.user, delivery_location=self.loc, total_amount=100, status='pending')

    def test_admin_order_list_requires_staff(self):
        # anonymous -> redirect to login
        from django.urls import reverse
        r = self.client.get(reverse('admin_order_list'))
        self.assertEqual(r.status_code, 302)
        # normal user cannot
        self.client.login(username='u', password='pass')
        r = self.client.get(reverse('admin_order_list'))
        self.assertEqual(r.status_code, 302)  # redirected to admin login (staff required)
        self.client.logout()
        # staff can access
        self.client.login(username='admin', password='pass')
        r = self.client.get(reverse('admin_order_list'))
        self.assertEqual(r.status_code, 200)

    def test_admin_can_update_order_status(self):
        from django.urls import reverse
        self.client.login(username='admin', password='pass')
        r = self.client.post(reverse('admin_order_detail', args=[self.order1.id]), {'status': 'confirmed'}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.order1.refresh_from_db()
        self.assertEqual(self.order1.status, 'confirmed')

    def test_admin_order_detail_contains_chat_link(self):
        self.client.login(username='admin', password='pass')
        from django.urls import reverse
        r = self.client.get(reverse('admin_order_detail', args=[self.order1.id]))
        self.assertEqual(r.status_code, 200)
        self.assertIn(f"/commande/{self.order1.id}/chat/", r.content.decode())

    def test_admin_nav_shows_unread_messages_count(self):
        # create conversation and unread message
        from .models import Conversation
        conv = Conversation.objects.create(order=self.order1)
        conv.participants.add(self.admin)
        conv.participants.add(self.user)
        Message.objects.create(conversation=conv, sender=self.user, content='Nouvel item')
        self.client.login(username='admin', password='pass')
        from django.urls import reverse
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)
        # check badge with count 1 present
        self.assertIn('<span class="badge bg-warning text-dark ms-2">1</span>', r.content.decode())

    def test_home_product_images_responsive(self):
        # product with an image path should render the responsive wrapper and img class
        from .models import Product
        p = Product.objects.create(name='Kibble', description='Tasty', price=10.0, image='products/test.jpg', stock=5)
        from django.urls import reverse
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode()
        # ensure our new wrapper and img class are present
        self.assertIn('class="product-image"', content)
        self.assertIn('class="product-image__img"', content)


# WebSocket / chat consumer tests
import asyncio
import unittest
try:
    from channels.testing import WebsocketCommunicator
    from croquettes_config.asgi import application
    HAS_CHANNELS = True
except Exception:
    HAS_CHANNELS = False

@unittest.skipUnless(HAS_CHANNELS, "channels/testing or its dependencies (daphne) are not available")
@override_settings(SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies')
class ChatConsumerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('client', 'c@example.com', 'pass')
        self.staff = User.objects.create_user('staff', 's@example.com', 'pass', is_staff=True)
        self.loc = DeliveryLocation.objects.create(name='Local2')
        self.order = Order.objects.create(user=self.user, delivery_location=self.loc, total_amount=50, status='pending')

    def _get_session_cookie(self, username, password):
        self.client.login(username=username, password=password)
        sessionid = self.client.cookies.get('sessionid').value
        self.client.logout()
        return sessionid

    def test_anonymous_cannot_connect(self):
        from django import db
        # Close test DB connection so ASGI thread can open its own connection without locking
        db.connection.close()
        communicator = WebsocketCommunicator(application, f"/ws/orders/{self.order.id}/")
        connected, _ = asyncio.get_event_loop().run_until_complete(communicator.connect())
        self.assertFalse(connected)
        asyncio.get_event_loop().run_until_complete(communicator.disconnect())

    def test_staff_can_create_message_via_consumer_helpers(self):
        # Test permission check and DB message creation via consumer helper methods (avoids threading/DB locking issues)
        from .consumers import OrderChatConsumer
        from asgiref.sync import async_to_sync

        consumer = OrderChatConsumer(scope={'user': self.staff})
        # Permission check
        allowed = async_to_sync(consumer._user_can_access_order)(self.staff, self.order.id)
        self.assertTrue(allowed)
        # Create message and check it is persisted
        msg = async_to_sync(consumer._create_message)(self.staff, self.order.id, 'Hello staff')
        self.assertEqual(msg.content, 'Hello staff')
        self.assertTrue(Message.objects.filter(id=msg.id).exists())
        # Notification should be created for the order owner
        self.assertTrue(Notification.objects.filter(recipient=self.user, verb__icontains=f"Nouveau message sur la commande #{self.order.id}").exists())

    def test_mark_notification_read(self):
        # create notification and mark as read via AJAX
        n = Notification.objects.create(recipient=self.user, verb='Test read', url='/')
        # login as the user in this test setup
        self.client.login(username='client', password='pass')
        from django.urls import reverse
        r = self.client.post(reverse('mark_notification_read', args=[n.id]))
        self.assertEqual(r.status_code, 200)
        n.refresh_from_db()
        self.assertFalse(n.unread)

    def test_admin_messages_list_and_reply(self):
        # create conversation and message from user
        from .models import Conversation
        conv = Conversation.objects.create(order=self.order)
        conv.participants.add(self.user)
        conv.participants.add(self.staff)
        msg = Message.objects.create(conversation=conv, sender=self.user, content='Bonjour')
        # staff should see the conversation
        self.client.login(username='staff', password='pass')
        from django.urls import reverse
        r = self.client.get(reverse('admin_messages_list'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(f"Commande #{self.order.id}", r.content.decode())
        # staff replies
        r = self.client.post(reverse('admin_message_detail', args=[conv.id]), {'message': 'Bonjour, en cours'}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Message.objects.filter(conversation=conv, content='Bonjour, en cours').exists())
        # a notification should be created for the user
        self.assertTrue(Notification.objects.filter(recipient=self.user, verb__icontains=f"Nouveau message sur la commande #{self.order.id}").exists())
