from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Coupon(models.Model):

    DISCOUNT_TYPES = (
        ("PERCENTAGE", "Percentage"),
        ("FIXED", "Fixed Amount"),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    maximum_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    usage_limit = models.PositiveIntegerField(
        default=1
    )

    used_count = models.PositiveIntegerField(
        default=0
    )

    valid_from = models.DateTimeField()

    valid_to = models.DateTimeField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()

        return (
            self.is_active
            and self.valid_from <= now <= self.valid_to
            and self.used_count < self.usage_limit
        )

    def get_discount(self, total):
        if total < self.minimum_order_amount:
            return Decimal("0.00")
        if self.discount_type == "PERCENTAGE":
            discount = total * (self.discount_value / Decimal("100"))
            if self.maximum_discount is not None:
                discount = min(discount, self.maximum_discount)
            return discount
        elif self.discount_type == "FIXED":
            return min(self.discount_value, total)
        return Decimal("0.00")

    def clean(self):
        if self.valid_from and self.valid_to and self.valid_from >= self.valid_to:
            raise ValidationError("Valid from must be before valid to.")

        if self.discount_type == "PERCENTAGE" and self.discount_value > 100:
            raise ValidationError("Percentage discount cannot exceed 100%.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
