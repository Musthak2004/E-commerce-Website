from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import models, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.models import Cart
from coupons.models import Coupon
from .models import Order, OrderItem


@require_POST
@login_required
def create_order(request):

    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    with transaction.atomic():

        items = list(cart.items.select_related("product").all())

        for item in items:
            product = item.product
            if not product.is_available or product.stock < item.quantity:
                messages.error(
                    request,
                    f'"{product.name}" is no longer available in the requested quantity.'
                )
                return redirect("cart:cart_detail")

        subtotal = sum(
            item.product.price * item.quantity
            for item in items
        )

        coupon_id = request.session.get("coupon_id")
        discount_amount = Decimal("0.00")
        applied_coupon = None
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, is_active=True)
                if coupon.is_valid:
                    discount_amount = coupon.get_discount(subtotal)
                    applied_coupon = coupon
            except Coupon.DoesNotExist:
                del request.session["coupon_id"]

        order = Order.objects.create(
            user=request.user,
            total_price=subtotal - discount_amount,
            discount_amount=discount_amount,
            coupon=applied_coupon,
        )

        order_items = []
        for item in items:
            product = item.product
            product.stock -= item.quantity
            product.save(update_fields=["stock"])
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price,
                )
            )
        OrderItem.objects.bulk_create(order_items)

        if applied_coupon:
            Coupon.objects.filter(id=applied_coupon.id).update(
                used_count=models.F("used_count") + 1
            )
            if "coupon_id" in request.session:
                del request.session["coupon_id"]

        cart.items.all().delete()

    try:
        send_mail(
            subject=f"Order Confirmed — #{order.id}",
            message=(
                f"Hi {order.user.email},\n\n"
                f"Your order #{order.id} has been placed successfully!\n\n"
                f"Total: ${order.total_price}\n"
                f"Status: {order.get_status_display()}\n\n"
                f"Thank you for shopping with ShopEase!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True,
        )
    except Exception:
        pass

    messages.success(request, "Order placed successfully!")
    return redirect("orders:order_detail", order.id)


@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )

    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def order_list(request):

    orders = Order.objects.filter(user=request.user).prefetch_related("items__product")

    return render(request, "orders/order_list.html", {"orders": orders})