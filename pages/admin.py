from django.contrib import admin

from .models import ContactMessage, NewsletterSubscriber


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "created_at"]
    list_filter = ["subject", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["created_at"]


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "subscribed_at", "is_active"]
    list_filter = ["is_active", "subscribed_at"]
    search_fields = ["email"]
