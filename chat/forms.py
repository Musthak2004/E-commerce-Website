from django import forms

from .models import Message, MESSAGE_MAX_LENGTH


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Type your message...",
                "class": "chat-input",
                "maxlength": MESSAGE_MAX_LENGTH,
            })
        }

    def clean_body(self):
        body = self.cleaned_data.get("body", "").strip()
        if not body:
            raise forms.ValidationError("Message cannot be empty.")
        if len(body) > MESSAGE_MAX_LENGTH:
            raise forms.ValidationError(
                f"Message is too long (max {MESSAGE_MAX_LENGTH} characters)."
            )
        return body
