from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from products.models import Product, Category
from chat.models import Conversation, Message

User = get_user_model()

CSRF_HEADER = {"HTTP_X_CSRFTOKEN": "test"}


def _create_users():
    buyer = User.objects.create_user(
        email="buyer@test.com", username="buyer", password="testpass123"
    )
    seller = User.objects.create_user(
        email="seller@test.com", username="seller", password="testpass123",
        user_type="SELLER"
    )
    stranger = User.objects.create_user(
        email="stranger@test.com", username="stranger", password="testpass123"
    )
    return buyer, seller, stranger


def _create_product(seller):
    cat = Category.objects.create(name="Cat", slug="cat")
    return Product.objects.create(
        name="Product", slug="product", seller=seller,
        category=cat, price=10.00, stock=100
    )


def _create_conversation(buyer, seller, product):
    return Conversation.objects.create(
        buyer=buyer, seller=seller, product=product
    )


class InboxViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer, cls.seller, cls.stranger = _create_users()
        cls.product = _create_product(cls.seller)
        cls.conv = _create_conversation(cls.buyer, cls.seller, cls.product)
        Message.objects.create(
            conversation=cls.conv, sender=cls.buyer, body="Hey"
        )

    def test_inbox_shows_user_conversations(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hey")

    def test_inbox_empty_for_user_with_no_conversations(self):
        self.client.force_login(self.stranger)
        response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No conversations yet")

    def test_inbox_redirects_unauthenticated(self):
        response = self.client.get(reverse("chat:inbox"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('chat:inbox')}"
        )

    def test_inbox_seller_sees_conversations(self):
        self.client.force_login(self.seller)
        response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(response.status_code, 200)

    def test_inbox_pagination_exists(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(response.status_code, 200)


class ConversationDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer, cls.seller, cls.stranger = _create_users()
        cls.product = _create_product(cls.seller)
        cls.conv = _create_conversation(cls.buyer, cls.seller, cls.product)

    def test_participant_can_view(self):
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[self.conv.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_non_participant_gets_403(self):
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse("chat:detail", args=[self.conv.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_conversation_not_found_404(self):
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_marks_received_messages_as_read(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.seller, body="Unread"
        )
        self.assertFalse(Message.objects.get(pk=msg.pk).is_read)
        self.client.force_login(self.buyer)
        self.client.get(reverse("chat:detail", args=[self.conv.id]))
        self.assertTrue(Message.objects.get(pk=msg.pk).is_read)

    def test_senders_own_messages_not_marked_read(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="My own"
        )
        self.client.force_login(self.buyer)
        self.client.get(reverse("chat:detail", args=[self.conv.id]))
        self.assertFalse(Message.objects.get(pk=msg.pk).is_read)

    def test_empty_conversation_renders_send_form(self):
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[self.conv.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send")

    def test_shows_last_50_messages(self):
        for i in range(60):
            Message.objects.create(
                conversation=self.conv, sender=self.seller,
                body=f"Message {i}"
            )
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("chat:detail", args=[self.conv.id])
        )
        self.assertEqual(response.status_code, 200)
        # Should have 50 messages visible
        self.assertContains(response, "Message 59")
        self.assertNotContains(response, "Message 9")


class SendMessageViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer, cls.seller, cls.stranger = _create_users()
        cls.product = _create_product(cls.seller)
        cls.conv = _create_conversation(cls.buyer, cls.seller, cls.product)

    def setUp(self):
        cache.clear()

    def test_send_message_creates_message(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("chat:send", args=[self.conv.id]),
            {"body": "Hello!"},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.conv.messages.count(), 1)
        self.assertEqual(self.conv.messages.first().body, "Hello!")

    def test_send_empty_body_returns_error(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("chat:send", args=[self.conv.id]),
            {"body": ""},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 422)

    def test_send_whitespace_only_body_returns_error(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("chat:send", args=[self.conv.id]),
            {"body": "   "},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 422)

    def test_send_long_body_rejected(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("chat:send", args=[self.conv.id]),
            {"body": "A" * 2001},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 422)

    def test_send_body_exactly_2000_accepted(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("chat:send", args=[self.conv.id]),
            {"body": "B" * 2000},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 200)

    def test_non_participant_cannot_send(self):
        self.client.force_login(self.stranger)
        response = self.client.post(
            reverse("chat:send", args=[self.conv.id]),
            {"body": "Hello"},
            **CSRF_HEADER
        )
        self.assertEqual(response.status_code, 403)
