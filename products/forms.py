from django import forms
from django.core.validators import MinValueValidator

from .models import Product


class ProductForm(forms.ModelForm):

    class Meta:

        model = Product

        fields = (
            "category",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "image",
            "is_available",
        )

    def clean_price(self):

        price = self.cleaned_data.get("price")

        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")

        return price

    def clean_stock(self):

        stock = self.cleaned_data.get("stock")

        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")

        return stock