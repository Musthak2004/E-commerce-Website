from django import forms
from django.core.exceptions import ValidationError

from .models import Payment


class PaymentForm(forms.ModelForm):

    class Meta:

        model = Payment

        fields = (
            "payment_method",
        )

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop("order", None)
        super().__init__(*args, **kwargs)
        if self.order:
            self.fields["payment_method"].help_text = (
                f"Total amount: ${self.order.total_price}"
            )

    def clean_payment_method(self):
        method = self.cleaned_data["payment_method"]

        if self.order and self.order.total_price <= 0:
            raise ValidationError("Cannot process payment for a zero-value order.")

        if self.order:
            try:
                self.order.payment
                raise ValidationError("This order already has a payment record.")
            except Payment.DoesNotExist:
                pass

        return method