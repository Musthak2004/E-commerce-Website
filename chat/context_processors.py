from .models import Conversation, Message


def chat_unread_count(request):
    """Inject unread_chat_count into all templates for the nav badge."""
    if not request.user.is_authenticated:
        return {"unread_chat_count": None}

    count = Message.objects.filter(
        conversation__in=Conversation.for_user(request.user),
        is_read=False,
    ).exclude(
        sender=request.user,
    ).count()

    return {"unread_chat_count": count}
