from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "minimum_order_amount",
        "usage_limit",
        "used_count",
        "valid_from",
        "valid_to",
        "is_active",
    )

    list_filter = (
        "discount_type",
        "is_active",
        "valid_from",
        "valid_to",
    )

    list_editable = (
        "is_active",
    )

    search_fields = (
        "code",
    )

    readonly_fields = (
        "used_count",
        "created_at",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )
