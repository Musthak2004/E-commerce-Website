from django import forms

from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Type your message...",
                "class": "chat-input",
                "maxlength": 2000,
            })
        }

    def clean_body(self):
        body = self.cleaned_data.get("body", "").strip()
        if not body:
            raise forms.ValidationError("Message cannot be empty.")
        if len(body) > 2000:
            raise forms.ValidationError("Message is too long (max 2000 characters).")
        return body
