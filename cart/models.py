from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, F

from accounts.models import CustomUser
from products.models import Product


class AbandonedCartReminder(models.Model):
    """Tracks reminder emails sent for abandoned carts.

    Used by the `send_abandoned_cart_reminders` management command to
    avoid sending duplicate reminders and to track recovery rates.
    """

    REMINDER_TYPES = (
        ("FIRST", "First reminder"),
        ("SECOND", "Second reminder"),
        ("FINAL", "Final reminder"),
    )

    cart = models.ForeignKey(
        "Cart",
        on_delete=models.CASCADE,
        related_name="reminders",
    )

    reminder_type = models.CharField(
        max_length=10,
        choices=REMINDER_TYPES,
        default="FIRST",
    )

    sent_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    recovered = models.BooleanField(
        default=False,
        help_text="Did the user place an order after this reminder?",
    )

    recovered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-sent_at",)
        verbose_name = "Abandoned Cart Reminder"
        verbose_name_plural = "Abandoned Cart Reminders"
        indexes = (
            models.Index(fields=("cart", "reminder_type")),
        )

    def __str__(self):
        return (
            f"{self.get_reminder_type_display()} for "
            f"cart #{self.cart_id} ({self.cart.user.email})"
        )


class Wishlist(models.Model):

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="wishlist"
    )

    products = models.ManyToManyField(
        Product,
        related_name="wishlists",
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Wishlist - {self.user.email}"


class Cart(models.Model):

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="cart"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Cart - {self.user.email}"

    @property
    def total_price(self):
        result = self.items.aggregate(
            total=Sum(F("product__price") * F("quantity"))
        )
        return result["total"] or 0


class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_cart_product"
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def total_price(self):

        return (
            self.product.price *
            self.quantity
        )