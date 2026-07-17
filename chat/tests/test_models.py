from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product, Category
from chat.models import Conversation, Message

User = get_user_model()


class ConversationModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = User.objects.create_user(
            email="buyer@test.com", username="buyer", password="testpass123"
        )
        cls.seller = User.objects.create_user(
            email="seller@test.com", username="seller", password="testpass123",
            user_type="SELLER"
        )
        cls.category = Category.objects.create(name="Test Cat", slug="test-cat")
        cls.product = Product.objects.create(
            name="Test Product", slug="test-product", seller=cls.seller,
            category=cls.category, price=10.00, stock=100
        )

    def test_create_conversation(self):
        conv = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=self.product
        )
        self.assertEqual(conv.buyer, self.buyer)
        self.assertEqual(conv.seller, self.seller)
        self.assertEqual(conv.product, self.product)
        self.assertIsNotNone(conv.created_at)
        self.assertIsNotNone(conv.updated_at)

    def test_conversation_str(self):
        conv = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=self.product
        )
        expected = f"Conversation({self.buyer.id} x {self.seller.id}, product={self.product.id})"
        self.assertEqual(str(conv), expected)

    def test_unique_constraint_buyer_seller_product(self):
        Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=self.product
        )
        with self.assertRaises(IntegrityError):
            Conversation.objects.create(
                buyer=self.buyer, seller=self.seller, product=self.product
            )

    def test_unique_constraint_store_conversation(self):
        """Two users can only have one store-general (product-less) conversation."""
        Conversation.objects.create(buyer=self.buyer, seller=self.seller)
        with self.assertRaises(IntegrityError):
            Conversation.objects.create(buyer=self.buyer, seller=self.seller)

    def test_different_product_creates_new_conversation(self):
        """Same buyer/seller about a different product is a different conversation."""
        product2 = Product.objects.create(
            name="Another", slug="another", seller=self.seller,
            category=self.category, price=5.00, stock=50
        )
        conv1 = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=self.product
        )
        conv2 = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=product2
        )
        self.assertNotEqual(conv1.id, conv2.id)

    def test_buyer_deleted_sets_null(self):
        """D21: Deleting a user sets buyer/seller to NULL, preserves conversation."""
        conv = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=self.product
        )
        self.buyer.delete()
        conv.refresh_from_db()
        self.assertIsNone(conv.buyer)

    def test_seller_deleted_sets_null(self):
        """D21: Deleting seller preserves conversation with null seller."""
        conv = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, product=self.product
        )
        self.seller.delete()
        conv.refresh_from_db()
        self.assertIsNone(conv.seller)


class MessageModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = User.objects.create_user(
            email="buyer@test.com", username="buyer", password="testpass123"
        )
        cls.seller = User.objects.create_user(
            email="seller@test.com", username="seller", password="testpass123",
            user_type="SELLER"
        )
        cls.category = Category.objects.create(name="Test Cat", slug="test-cat")
        cls.product = Product.objects.create(
            name="Test Product", slug="test-product", seller=cls.seller,
            category=cls.category, price=10.00, stock=100
        )
        cls.conv = Conversation.objects.create(
            buyer=cls.buyer, seller=cls.seller, product=cls.product
        )

    def test_create_message(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="Hello"
        )
        self.assertEqual(msg.conversation, self.conv)
        self.assertEqual(msg.sender, self.buyer)
        self.assertEqual(msg.body, "Hello")
        self.assertFalse(msg.is_read)
        self.assertIsNotNone(msg.created_at)

    def test_message_str(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="Hi there"
        )
        expected = f"Message({msg.id}) by {self.buyer.id} in conv {self.conv.id}"
        self.assertEqual(str(msg), expected)

    def test_message_default_is_read_false(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="Hello"
        )
        self.assertFalse(msg.is_read)

    def test_message_ordering(self):
        msg1 = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="First"
        )
        msg2 = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="Second"
        )
        messages = self.conv.messages.all()
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)

    def test_sender_deleted_sets_null(self):
        msg = Message.objects.create(
            conversation=self.conv, sender=self.buyer, body="Test"
        )
        self.buyer.delete()
        msg.refresh_from_db()
        self.assertIsNone(msg.sender)

    def test_composite_index_query(self):
        """Verify the composite index works (smoke test)."""
        for i in range(5):
            Message.objects.create(
                conversation=self.conv,
                sender=self.buyer if i % 2 == 0 else self.seller,
                body=f"Message {i}"
            )
        msgs = list(self.conv.messages.order_by("-created_at"))
        self.assertEqual(len(msgs), 5)
        # Most recent first
        self.assertIn("Message 4", msgs[0].body)
