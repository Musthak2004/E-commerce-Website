from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "amount",
        "payment_method",
        "status",
        "paid_at",
    )

    list_filter = (
        "status",
        "payment_method",
    )

    search_fields = (
        "transaction_id",
        "order__id",
    )

    list_select_related = (
        "order",
    )

    readonly_fields = (
        "transaction_id",
        "paid_at",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )