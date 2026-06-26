from django import forms


class CouponApplyForm(forms.Form):

    code = forms.CharField(
        max_length=50,
        label="Coupon Code",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter coupon code",
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data["code"]
        return code.strip().upper()
