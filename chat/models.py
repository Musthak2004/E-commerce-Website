from django.db import models
from django.conf import settings
from django.db.models import UniqueConstraint, Q


MESSAGE_MAX_LENGTH = 2000


class Conversation(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,          # D21: SET_NULL preserves surviving participant's history
        on_delete=models.SET_NULL,
        related_name="conversations_as_buyer"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,          # D21
        on_delete=models.SET_NULL,
        related_name="conversations_as_seller"
    )
    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # D16: touched on new message for cachalot

    @classmethod
    def for_user(cls, user):
        """Return conversations involving the given user as buyer or seller."""
        return cls.objects.filter(Q(buyer=user) | Q(seller=user))

    def mark_messages_read(self, user):
        """Mark all unread messages not sent by *user* as read in this conversation."""
        return self.messages.filter(
            is_read=False,
        ).exclude(
            sender=user,
        ).update(is_read=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["buyer", "seller", "product"],
                name="unique_conversation_per_product"
            ),
            UniqueConstraint(
                fields=["buyer", "seller"],
                condition=Q(product__isnull=True),
                name="unique_store_conversation"
            ),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation({self.buyer_id} x {self.seller_id}, product={self.product_id})"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,          # SET_NULL safety net
        on_delete=models.SET_NULL,
        related_name="sent_messages"
    )
    body = models.TextField(max_length=MESSAGE_MAX_LENGTH)  # DoS protection
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "-created_at"])
        ]

    def __str__(self):
        return f"Message({self.id}) by {self.sender_id} in conv {self.conversation_id}"
