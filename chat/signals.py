from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Conversation, Message
from products.models import Product


@receiver(post_save, sender=Message)
def touch_conversation_on_message(sender, instance, **kwargs):
    """D16: Touch conversation.updated_at to invalidate cachalot cache"""
    Conversation.objects.filter(pk=instance.conversation_id).update(updated_at=timezone.now())


@receiver(post_save, sender=Product)
def reassign_conversation_seller(sender, instance, **kwargs):
    """D23: Keep Conversation.seller in sync when Product.seller changes"""
    if instance.seller is not None:
        Conversation.objects.filter(product=instance).exclude(seller=instance.seller).update(seller=instance.seller)
