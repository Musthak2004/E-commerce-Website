from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
)
from django.db.models import Prefetch
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import (
    require_POST,
)

from coupons.models import Coupon

from .models import (
    Cart,
    CartItem,
    Wishlist,
)

from products.models import Product


@require_POST
@login_required
def add_to_cart(
    request,
    product_id
):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    cart, created = (
        Cart.objects.get_or_create(
            user=request.user
        )
    )

    item, created = (
        CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )
    )

    if not created:
        item.quantity += 1
        item.save()

    messages.success(
        request,
        f"{product.name} added to your cart."
    )

    return redirect(
        "cart:cart_detail"
    )


@require_POST
@login_required
def remove_from_cart(
    request,
    item_id
):

    item = get_object_or_404(
        CartItem.objects.select_related("product"),
        id=item_id,
        cart__user=request.user
    )

    product_name = item.product.name

    item.delete()

    messages.success(
        request,
        f"{product_name} removed from your cart."
    )

    return redirect(
        "cart:cart_detail"
    )


@require_POST
@login_required
def update_quantity(
    request,
    item_id
):

    item = get_object_or_404(
        CartItem.objects.select_related("product"),
        id=item_id,
        cart__user=request.user
    )

    try:
        quantity = int(
            request.POST.get("quantity", 1)
        )
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    item.quantity = quantity

    item.save()

    messages.success(
        request,
        f"{item.product.name} quantity updated."
    )

    return redirect(
        "cart:cart_detail"
    )


@login_required
def cart_detail(
    request
):

    cart = Cart.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=CartItem.objects.select_related(
                "product__category"
            )
        )
    ).filter(
        user=request.user
    ).first()

    coupon = None
    discount_amount = 0
    total_after_discount = 0

    if cart:
        coupon_id = request.session.get("coupon_id")

        if coupon_id:
            try:
                coupon = Coupon.objects.get(
                    id=coupon_id,
                    is_active=True,
                )
                if coupon.is_valid:
                    discount_amount = coupon.get_discount(cart.total_price)
            except Coupon.DoesNotExist:
                del request.session["coupon_id"]

        total_after_discount = max(cart.total_price - discount_amount, 0)

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart": cart,
            "coupon": coupon,
            "discount_amount": discount_amount,
            "total_after_discount": total_after_discount,
        }
    )


@require_POST
@login_required
def toggle_wishlist(request, product_id):

    product = get_object_or_404(Product, id=product_id, is_available=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(id=product_id).exists():
        wishlist.products.remove(product)
        messages.success(request, f"{product.name} removed from your wishlist.")
    else:
        wishlist.products.add(product)
        messages.success(request, f"{product.name} added to your wishlist.")

    return redirect(request.META.get("HTTP_REFERER", "products:product_list"))
