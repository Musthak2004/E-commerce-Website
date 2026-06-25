from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.models import Cart
from .models import Order, OrderItem


@require_POST
@login_required
def create_order(request):

    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    items = cart.items.select_related("product").all()

    for item in items:
        if not item.product.is_available or item.product.stock < item.quantity:
            messages.error(
                request,
                f'"{item.product.name}" is no longer available in the requested quantity.'
            )
            return redirect("cart:cart_detail")

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            total_price=cart.total_price
        )

        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
            for item in items
        ]
        OrderItem.objects.bulk_create(order_items)

        cart.items.all().delete()

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