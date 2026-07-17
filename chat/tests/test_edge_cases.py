from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.template import Template, Context

from products.models import Product, Category
from chat.models import Conversation, Message

User = get_user_model()

CSRF_HEADER = {"HTTP_X_CSRFTOKEN": "test"}


class EdgeCaseTests(TestCase):
    def setUp(self):
        cache.clear()

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

    def test_template_xss_escaping(self):
        """HTML in message body should be auto-escaped by Django templates."""
        msg = Message.objects.create(
            conversation=self.conv, sender=self.seller,
            body='<script>alert("xss")</script>'
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[self.conv.id])
        )
        self.assertContains(response, "&lt;script&gt;")
        # Check the message body specifically doesn't contain raw HTML tags
        self.assertContains(response, "&lt;script&gt;alert")

    def test_null_sender_does_not_crash_template(self):
        """D14: Message with null sender renders 'Deleted User' fallback."""
        msg = Message.objects.create(
            conversation=self.conv, sender=None, body="From deleted user"
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[self.conv.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Deleted User")

    def test_null_sender_in_message_list_partial(self):
        """D14: Partial renders 'Deleted User' for null sender."""
        msg = Message.objects.create(
            conversation=self.conv, sender=None, body="Deleted"
        )
        template = Template(
            "{% load static %}"
            "{% include 'chat/partials/message_list.html' %}"
        )
        rendered = template.render(Context({
            "messages": [msg],
            "request": type("Req", (), {"user": self.buyer})(),
        }))
        self.assertIn("Deleted User", rendered)

    def test_null_product_does_not_crash_inbox(self):
        """D15: Conversation with deleted product renders safely."""
        # Delete the product from the default conversation to trigger null
        self.product.delete()
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(response.status_code, 200)
        # Should not crash — product reference is null-guarded in template
        # and the inbox-item-product div is only shown when product exists

    def test_null_product_in_conversation_detail(self):
        """D15: Conversation detail handles null product gracefully."""
        conv = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=None
        )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[conv.id])
        )
        self.assertEqual(response.status_code, 200)
        # Should NOT crash on product reference
        self.assertNotContains(response, "Regarding:")

    def test_seller_reassignment_updates_conversation(self):
        """D23: Changing product.seller updates conversation.seller via signal."""
        new_seller = User.objects.create_user(
            email="newseller@test.com", username="newseller",
            password="testpass123", user_type="SELLER"
        )
        self.product.seller = new_seller
        self.product.save()
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.seller, new_seller)

    def test_rate_limit_on_send(self):
        """D24: Sending 31+ messages returns 429."""
        self.client.force_login(self.buyer)
        for i in range(30):
            response = self.client.post(
                reverse("chat:send", args=[self.conv.id]),
                {"body": f"Message {i}"},
                **CSRF_HEADER
            )
            self.assertEqual(response.status_code, 200, f"Failed on msg {i}")
        # 31st message should be rate-limited
        response = self.client.post(
            reverse("chat:send", args=[self.conv.id]),
            {"body": "Rate limited?"},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 429)

    def test_empty_conversation_shows_empty_state(self):
        """An empty conversation shows the 'No messages yet' prompt."""
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[self.conv.id])
        )
        self.assertContains(response, "No messages yet")

    def test_conversation_updated_at_changes_on_new_message(self):
        """D16: Sending a message touches conversation.updated_at."""
        old_updated = self.conv.updated_at
        Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="New msg"
        )
        self.conv.refresh_from_db()
        self.assertGreater(self.conv.updated_at, old_updated)
