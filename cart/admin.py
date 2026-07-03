from django.contrib import admin

from .models import (
    AbandonedCartReminder,
    Cart,
    CartItem,
    Wishlist,
)


class CartItemInline(
    admin.TabularInline
):

    model = CartItem

    extra = 0

    readonly_fields = (
        "total_price",
    )


@admin.register(Cart)
class CartAdmin(
    admin.ModelAdmin
):

    list_display = (
        "user",
        "item_count",
        "total_price",
        "created_at",
    )

    list_select_related = ("user",)

    search_fields = ("user__email",)

    inlines = [
        CartItemInline
    ]

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()


@admin.register(CartItem)
class CartItemAdmin(
    admin.ModelAdmin
):

    list_display = (
        "cart",
        "product",
        "quantity",
        "total_price",
    )

    list_select_related = (
        "cart",
        "cart__user",
        "product",
    )

    search_fields = (
        "cart__user__email",
        "product__name",
    )

    list_filter = ("product",)

    readonly_fields = ("total_price",)


@admin.register(Wishlist)
class WishlistAdmin(
    admin.ModelAdmin
):

    list_display = (
        "user",
        "item_count",
    )

    list_select_related = ("user",)

    search_fields = ("user__email",)

    filter_horizontal = ("products",)

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.products.count()


@admin.register(AbandonedCartReminder)
class AbandonedCartReminderAdmin(admin.ModelAdmin):

    list_display = (
        "cart",
        "user_email",
        "reminder_type",
        "sent_at",
        "recovered",
        "recovered_at",
    )

    list_select_related = ("cart__user",)

    search_fields = ("cart__user__email",)

    list_filter = ("reminder_type", "recovered", "sent_at")

    readonly_fields = ("sent_at", "recovered_at")

    @admin.display(description="User")
    def user_email(self, obj):
        return obj.cart.user.email