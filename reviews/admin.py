from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "product",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
        "product",
    )

    search_fields = (
        "user__email",
        "product__name",
    )

    list_select_related = (
        "user",
        "product",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )