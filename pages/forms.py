from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "John Doe"}),
            "email": forms.EmailInput(attrs={"placeholder": "john@example.com"}),
            "subject": forms.Select(
                choices=[
                    ("", "Select a topic"),
                    ("general", "General Inquiry"),
                    ("order", "Order Support"),
                    ("product", "Product Question"),
                    ("return", "Returns & Exchanges"),
                    ("other", "Other"),
                ]
            ),
            "message": forms.Textarea(attrs={"placeholder": "How can we help you?"}),
        }
