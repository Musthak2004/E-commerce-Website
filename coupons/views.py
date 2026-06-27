from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .forms import CouponApplyForm
from .models import Coupon


@require_POST
@login_required
def apply_coupon(request):

    form = CouponApplyForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data["code"]

        try:
            coupon = Coupon.objects.get(code__iexact=code)
            if coupon.is_valid:
                request.session["coupon_id"] = coupon.id
                messages.success(
                    request,
                    f'Coupon "{coupon.code}" applied successfully.'
                )
            else:
                messages.error(request, "Coupon is invalid or expired.")
        except Coupon.DoesNotExist:
            messages.error(request, "Coupon not found.")
    else:
        messages.error(request, "Please enter a valid coupon code.")

    return redirect("cart:cart_detail")


@require_POST
@login_required
def remove_coupon(request):

    if "coupon_id" in request.session:
        del request.session["coupon_id"]

    messages.success(
        request,
        "Coupon removed."
    )

    return redirect("cart:cart_detail")
