from django import forms
from django.core.exceptions import ValidationError

from .models import Review


class ReviewForm(forms.ModelForm):

    class Meta:

        model = Review

        fields = (
            "rating",
            "comment",
        )

        widgets = {
            "rating": forms.Select(
                attrs={"class": "rating-select"}
            ),
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share your thoughts about this product…",
                }
            ),
        }

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if rating not in (1, 2, 3, 4, 5):
            raise ValidationError("Rating must be between 1 and 5.")
        return rating

    def clean_comment(self):
        comment = self.cleaned_data["comment"]
        stripped = comment.strip()
        if len(stripped) > 0 and len(stripped) < 10:
            raise ValidationError("Comment is too short (minimum 10 characters).")
        return stripped