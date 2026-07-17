from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("start/<int:product_id>/", views.start_conversation, name="start"),
    path("<int:conversation_id>/", views.conversation_detail, name="detail"),
    path("<int:conversation_id>/send/", views.send_message, name="send"),
    path("api/<int:conversation_id>/messages/", views.poll_messages, name="poll"),
    path("api/<int:conversation_id>/older/", views.older_messages, name="older"),
    path("api/<int:conversation_id>/mark-read/", views.mark_read, name="mark_read"),
]
