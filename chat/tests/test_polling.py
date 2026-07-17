from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse

from products.models import Product, Category
from chat.models import Conversation, Message

User = get_user_model()

CSRF_HEADER = {"HTTP_X_CSRFTOKEN": "test"}


class PollEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = User.objects.create_user(
            email="buyer@test.com", username="buyer", password="testpass123"
        )
        cls.seller = User.objects.create_user(
            email="seller@test.com", username="seller", password="testpass123",
            user_type="SELLER"
        )
        cls.category = Category.objects.create(name="Cat", slug="cat")
        cls.product = Product.objects.create(
            name="Product", slug="product", seller=cls.seller,
            category=cls.category, price=10.00, stock=100
        )
        cls.conv = Conversation.objects.create(
            buyer=cls.buyer, seller=cls.seller, product=cls.product
        )

    def setUp(self):
        cache.clear()

    def test_poll_after_n_returns_new_messages(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.seller, body="New"
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": msg.id - 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New")

    def test_poll_after_max_returns_empty(self):
        Message.objects.create(
            conversation=self.conv, sender=self.seller, body="Test"
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 999999}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test")

    def test_poll_after_zero_returns_recent_messages(self):
        for i in range(55):
            Message.objects.create(
                conversation=self.conv, sender=self.seller,
                body=f"Msg {i}"
            )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 0}
        )
        self.assertEqual(response.status_code, 200)
        # Capped at 50 — first 50 messages (Msg 0-49) returned
        self.assertContains(response, "Msg 49")
        self.assertNotContains(response, "Msg 54")

    def test_poll_excludes_senders_own_messages(self):
        """D9: Poll must NOT return the sender's own messages."""
        msg_from_buyer = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="From buyer"
        )
        msg_from_seller = Message.objects.create(
            conversation=self.conv, sender=self.seller, body="From seller"
        )
        # Buyer polls — should not see their own message
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 0}
        )
        self.assertContains(response, "From seller")
        self.assertNotContains(response, "From buyer")

    def test_poll_seller_excludes_their_own_messages(self):
        msg_from_buyer = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="From buyer"
        )
        msg_from_seller = Message.objects.create(
            conversation=self.conv, sender=self.seller, body="From seller"
        )
        # Seller polls — should not see their own message
        self.client.force_login(self.seller)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 0}
        )
        self.assertContains(response, "From buyer")
        self.assertNotContains(response, "From seller")

    def test_poll_returns_405_on_post(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 0},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 405)

    def test_poll_has_never_cache_header(self):
        Message.objects.create(
            conversation=self.conv, sender=self.seller, body="Test"
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 0}
        )
        self.assertIn("Cache-Control", response)
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertIn("max-age=0", response["Cache-Control"])

    def test_poll_negative_after_handled_gracefully(self):
        """D22: Negative after param defaults to 0."""
        Message.objects.create(
            conversation=self.conv, sender=self.seller, body="Test"
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": -1}
        )
        self.assertEqual(response.status_code, 200)

    def test_poll_without_after_returns_last_50(self):
        for i in range(60):
            Message.objects.create(
                conversation=self.conv, sender=self.seller,
                body=f"Msg {i}"
            )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id])
        )
        self.assertEqual(response.status_code, 200)
        # Should cap at 50 — first 50 messages (Msg 0-49) returned
        self.assertContains(response, "Msg 49")
        self.assertNotContains(response, "Msg 55")

    def test_poll_does_not_mark_messages_as_read(self):
        """D20: Poll is GET-only, does not mark read. Separate mark_read endpoint does."""
        msg = Message.objects.create(
            conversation=self.conv, sender=self.seller, body="Unread"
        )
        self.client.force_login(self.buyer)
        self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 0}
        )
        self.assertFalse(Message.objects.get(pk=msg.pk).is_read)

    def test_non_participant_poll_403(self):
        stranger = User.objects.create_user(
            email="stranger@test.com", username="stranger", password="testpass123"
        )
        self.client.force_login(stranger)
        response = self.client.get(
            reverse("chat:poll", args=[self.conv.id]),
            {"after": 0}
        )
        self.assertEqual(response.status_code, 403)


class MarkReadEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = User.objects.create_user(
            email="buyer@test.com", username="buyer", password="testpass123"
        )
        cls.seller = User.objects.create_user(
            email="seller@test.com", username="seller", password="testpass123",
            user_type="SELLER"
        )
        cls.category = Category.objects.create(name="Cat", slug="cat")
        cls.product = Product.objects.create(
            name="Product", slug="product", seller=cls.seller,
            category=cls.category, price=10.00, stock=100
        )
        cls.conv = Conversation.objects.create(
            buyer=cls.buyer, seller=cls.seller, product=cls.product
        )

    def test_mark_read_marks_received_messages(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.seller, body="Unread"
        )
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("chat:mark_read", args=[self.conv.id]),
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Message.objects.get(pk=msg.pk).is_read)

    def test_mark_read_does_not_mark_own_messages(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="My own"
        )
        self.client.force_login(self.buyer)
        self.client.post(
            reverse("chat:mark_read", args=[self.conv.id]),
            **CSRF_HEADER
        )
        self.assertFalse(Message.objects.get(pk=msg.pk).is_read)

    def test_mark_read_non_participant_403(self):
        stranger = User.objects.create_user(
            email="stranger@test.com", username="stranger", password="testpass123"
        )
        self.client.force_login(stranger)
        response = self.client.post(
            reverse("chat:mark_read", args=[self.conv.id]),
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 403)

    def test_mark_read_405_on_get(self):
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:mark_read", args=[self.conv.id])
        )
        self.assertEqual(response.status_code, 405)


class OlderMessagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = User.objects.create_user(
            email="buyer@test.com", username="buyer", password="testpass123"
        )
        cls.seller = User.objects.create_user(
            email="seller@test.com", username="seller", password="testpass123",
            user_type="SELLER"
        )
        cls.category = Category.objects.create(name="Cat", slug="cat")
        cls.product = Product.objects.create(
            name="Product", slug="product", seller=cls.seller,
            category=cls.category, price=10.00, stock=100
        )
        cls.conv = Conversation.objects.create(
            buyer=cls.buyer, seller=cls.seller, product=cls.product
        )

    def test_older_returns_messages_before_id(self):
        for i in range(10):
            Message.objects.create(
                conversation=self.conv, sender=self.seller,
                body=f"Msg {i}"
            )
        self.client.force_login(self.buyer)
        last = self.conv.messages.order_by("created_at").last()
        response = self.client.get(
            reverse("chat:older", args=[self.conv.id]),
            {"before": last.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Msg 8")
        self.assertNotContains(response, "Msg 9")

    def test_older_fewer_than_50(self):
        for i in range(5):
            Message.objects.create(
                conversation=self.conv, sender=self.seller,
                body=f"Msg {i}"
            )
        self.client.force_login(self.buyer)
        last = self.conv.messages.order_by("created_at").last()
        response = self.client.get(
            reverse("chat:older", args=[self.conv.id]),
            {"before": last.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Msg 3")

    def test_older_no_more_messages(self):
        """D27: No more messages returns empty response so HTMX skips swap."""
        msg = Message.objects.create(
            conversation=self.conv, sender=self.seller, body="Only"
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:older", args=[self.conv.id]),
            {"before": msg.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_older_missing_before_defaults_to_last(self):
        """D28: Missing before param defaults gracefully."""
        for i in range(5):
            Message.objects.create(
                conversation=self.conv, sender=self.seller,
                body=f"Msg {i}"
            )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:older", args=[self.conv.id])
        )
        # Should 200, not 500
        self.assertEqual(response.status_code, 200)

    def test_older_non_participant_403(self):
        stranger = User.objects.create_user(
            email="stranger@test.com", username="stranger", password="testpass123"
        )
        self.client.force_login(stranger)
        response = self.client.get(
            reverse("chat:older", args=[self.conv.id]),
            {"before": 1}
        )
        self.assertEqual(response.status_code, 403)
