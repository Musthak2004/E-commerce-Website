from django.core.exceptions import ValidationError
from django.db import models

from orders.models import Order


class Payment(models.Model):

    PAYMENT_METHODS = (
        ("CARD", "Credit / Debit Card"),
        ("PAYPAL", "PayPal"),
        ("BANK_TRANSFER", "Bank Transfer"),
        ("CASH_ON_DELIVERY", "Cash on Delivery"),
    )

    PAYMENT_STATUS = (
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS
    )

    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="PENDING"
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"Payment #{self.id} — Order #{self.order_id} ({self.get_status_display()})"

    def clean(self):
        if self.transaction_id == "":
            self.transaction_id = None

    def save(self, *args, **kwargs):
        if self.transaction_id == "":
            self.transaction_id = None
        super().save(*args, **kwargs)