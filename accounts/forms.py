from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class SignUpForm(UserCreationForm):

    class Meta:

        model = CustomUser

        fields = (
            "username",
            "email",
            "user_type",
            "phone_number",
            "password1",
            "password2",
        )

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")

        return email