import json

from datetime import datetime, timezone

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import (
    Count,
    OuterRef,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.views.decorators.http import (
    require_POST,
    require_safe,
)

from products.models import Product

from .forms import MessageForm
from .models import Conversation, Message


PAGE_SIZE = 25
MESSAGE_PAGE_SIZE = 50
RATE_LIMIT_MAX = 30
RATE_LIMIT_WINDOW = 60


def _require_participant(conv, user):
    """Raise PermissionDenied if *user* is not a participant in *conv*."""
    if user not in (conv.buyer, conv.seller):
        raise PermissionDenied("You are not a participant in this conversation.")


@login_required
def inbox(request):

    conversations = Conversation.for_user(
        request.user,
    ).select_related(
        "buyer", "seller", "product",
    )

    # Annotate with last message details via Subquery
    last_msg = Message.objects.filter(
        conversation=OuterRef("pk"),
    ).order_by("-created_at")

    conversations = conversations.annotate(
        last_message_text=Subquery(last_msg.values("body")[:1]),
        last_message_at=Coalesce(
            Subquery(last_msg.values("created_at")[:1]),
            Value(datetime.min.replace(tzinfo=timezone.utc)),
        ),
    )

    # Annotate unread count — messages not read and not sent by the current user
    unread_subquery = Message.objects.filter(
        conversation=OuterRef("pk"),
        is_read=False,
    ).exclude(
        sender=request.user,
    ).values("conversation").annotate(
        count=Count("pk"),
    ).values("count")

    conversations = conversations.annotate(
        unread_count=Coalesce(Subquery(unread_subquery), Value(0)),
    )

    conversations = conversations.order_by("-last_message_at")

    paginator = Paginator(conversations, PAGE_SIZE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "conversations": page_obj,
        "page_obj": page_obj,
    }

    return render(request, "chat/inbox.html", context)


@login_required
def start_conversation(request, product_id):

    product = get_object_or_404(Product, pk=product_id)

    if product.seller is None:
        raise PermissionDenied("This product has no seller.")

    if request.user == product.seller:
        raise PermissionDenied("You cannot start a conversation with yourself.")

    conversation, created = Conversation.objects.get_or_create(
        buyer=request.user,
        seller=product.seller,
        product=product,
    )

    return redirect("chat:detail", conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):

    conv = get_object_or_404(Conversation, pk=conversation_id)

    _require_participant(conv, request.user)

    # Fetch newest 50 messages in ascending order
    messages_qs = conv.messages.select_related(
        "sender",
    ).order_by("-created_at")[:MESSAGE_PAGE_SIZE]
    messages_list = list(messages_qs)
    messages_list.reverse()

    # Mark received messages as read
    conv.mark_messages_read(request.user)

    form = MessageForm()

    # Determine the other participant
    other_user = conv.buyer if request.user == conv.seller else conv.seller

    # Check if there are older messages
    first_message = conv.messages.order_by("created_at").first()
    has_older = bool(messages_list and first_message and messages_list[0].id != first_message.id)
    first_message_id = messages_list[0].id if messages_list else 0

    context = {
        "conversation": conv,
        "messages": messages_list,
        "form": form,
        "other_user": other_user,
        "has_older": has_older,
        "first_message_id": first_message_id,
    }

    return render(request, "chat/conversation.html", context)


@require_POST
@login_required
def send_message(request, conversation_id):

    conv = get_object_or_404(Conversation, pk=conversation_id)

    _require_participant(conv, request.user)

    # Rate limiting
    if not request.user.is_superuser:
        key = f"chat_rate_limit_{request.user.id}"
        count = cache.get(key, 0)
        if count >= RATE_LIMIT_MAX:
            return HttpResponse(
                "Rate limit exceeded. Wait a moment.",
                status=429,
            )
        cache.set(key, count + 1, RATE_LIMIT_WINDOW)

    form = MessageForm(request.POST)

    if not form.is_valid():
        html = render_to_string(
            "chat/partials/send_form_errors.html",
            {"form": form},
            request=request,
        )
        return HttpResponse(html, status=422)

    message = form.save(commit=False)
    message.sender = request.user
    message.conversation = conv
    message.save()

    html = render_to_string(
        "chat/partials/message_bubble.html",
        {"message": message, "request": request},
        request=request,
    )
    response = HttpResponse(html)
    response["HX-Trigger"] = json.dumps({
        "new-message": {
            "conversation_id": conv.id,
            "message_id": message.id,
        },
    })
    return response


@require_safe
@never_cache
@login_required
def poll_messages(request, conversation_id):

    conv = get_object_or_404(Conversation, pk=conversation_id)

    _require_participant(conv, request.user)

    try:
        after = int(request.GET.get("after", 0))
        after = max(after, 0)
    except (ValueError, TypeError):
        after = 0

    messages_qs = conv.messages.filter(
        id__gt=after,
    ).exclude(
        sender=request.user,
    ).select_related(
        "sender",
    ).order_by("created_at")[:MESSAGE_PAGE_SIZE]

    context = {
        "conversation": conv,
        "messages": list(messages_qs),
    }

    return render(request, "chat/partials/message_list.html", context)


@require_POST
@login_required
def mark_read(request, conversation_id):

    conv = get_object_or_404(Conversation, pk=conversation_id)

    _require_participant(conv, request.user)

    conv.mark_messages_read(request.user)

    return HttpResponse("")


@require_safe
@login_required
def older_messages(request, conversation_id):

    conv = get_object_or_404(Conversation, pk=conversation_id)

    _require_participant(conv, request.user)

    # Determine the "before" message ID
    before = request.GET.get("before")
    if before is None:
        last_msg = conv.messages.order_by("-created_at").first()
        if last_msg is None:
            before = 0
        else:
            before = last_msg.pk
    else:
        try:
            before = int(before)
        except (ValueError, TypeError):
            before = 0

    # Fetch MESSAGE_PAGE_SIZE messages older than before
    older = list(
        conv.messages.filter(
            id__lt=before,
        ).select_related(
            "sender",
        ).order_by("-created_at")[:MESSAGE_PAGE_SIZE]
    )
    older.reverse()  # Ascending order for the template

    has_more = len(older) >= MESSAGE_PAGE_SIZE

    context = {
        "conversation": conv,
        "messages": older,
    }

    response = render(request, "chat/partials/message_list.html", context)
    response["X-Has-More"] = "true" if has_more else "false"
    return response
