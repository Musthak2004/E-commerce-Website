import json

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
)
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.template.loader import render_to_string
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
from products.recommendations import get_frequently_bought_together


def _cart_badge_html(request):
    """Render the cart count badge partial for OOB swap."""
    cart_count = request.session.get("cart_count")
    from cart.context_processors import cart_counts
    counts = cart_counts(request)
    return render_to_string(
        "cart/partials/cart_badge.html",
        {"cart_count": counts.get("cart_count")},
    )


def _wishlist_badge_html(request):
    """Render the wishlist count badge partial for OOB swap."""
    from cart.context_processors import cart_counts
    counts = cart_counts(request)
    return render_to_string(
        "cart/partials/wishlist_badge.html",
        {"wishlist_count": counts.get("wishlist_count")},
    )


def _cart_summary_context(request, cart):
    """Build the context dict for the cart summary partial."""
    coupon = None
    discount_amount = 0
    total_after_discount = 0

    if cart:
        coupon_id = request.session.get("coupon_id")
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, is_active=True)
                if coupon.is_valid:
                    discount_amount = coupon.get_discount(cart.total_price)
            except Coupon.DoesNotExist:
                if "coupon_id" in request.session:
                    del request.session["coupon_id"]

        total_after_discount = max(cart.total_price - discount_amount, 0)

    return {
        "cart": cart,
        "coupon": coupon,
        "discount_amount": discount_amount,
        "total_after_discount": total_after_discount,
        "remaining_for_free_shipping": max(50 - cart.total_price, 0) if cart else 0,
        "shipping_progress_percent": min(cart.total_price / 50 * 100, 100) if cart else 0,
    }


@require_POST
@login_required
def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    cart, created = Cart.objects.get_or_create(user=request.user)

    # Support a quantity parameter from the product detail page
    try:
        qty = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        qty = 1
    qty = max(1, min(qty, product.stock))

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        item.quantity = min(item.quantity + qty, product.stock)
    else:
        item.quantity = qty
    item.save()

    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        badge_html = _cart_badge_html(request)
        response = HttpResponse(badge_html)
        messages.success(request, f"{product.name} added to your cart.")
        response["HX-Trigger"] = json.dumps({
            "show-toast": {"message": f"{product.name} added to cart!", "type": "success"},
        })
        return response

    messages.success(request, f"{product.name} added to your cart.")
    return redirect("cart:cart_detail")


@require_POST
@login_required
def remove_from_cart(request, item_id):

    item = get_object_or_404(
        CartItem.objects.select_related("product"),
        id=item_id,
        cart__user=request.user,
    )

    product_name = item.product.name
    item.delete()

    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        cart = Cart.objects.prefetch_related(
            Prefetch("items", queryset=CartItem.objects.select_related("product__category"))
        ).filter(user=request.user).first()
        ctx = _cart_summary_context(request, cart)
        ctx["cart"] = cart
        from cart.context_processors import cart_counts
        counts = cart_counts(request)
        ctx["cart_count"] = counts.get("cart_count")
        html = render_to_string("cart/partials/cart_content.html", ctx, request=request)
        response = HttpResponse(html)
        response["HX-Trigger"] = json.dumps({
            "show-toast": {"message": f"{product_name} removed from cart.", "type": "success"},
        })
        return response

    messages.success(request, f"{product_name} removed from your cart.")
    return redirect("cart:cart_detail")


@require_POST
@login_required
def update_quantity(request, item_id):

    item = get_object_or_404(
        CartItem.objects.select_related("product"),
        id=item_id,
        cart__user=request.user,
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    # Clamp to available stock
    if quantity > item.product.stock:
        quantity = item.product.stock

    item.quantity = quantity
    item.save()

    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        cart = item.cart
        ctx = _cart_summary_context(request, cart)
        html_parts = []

        # Updated row
        row_html = render_to_string(
            "cart/partials/cart_row.html",
            {"item": item},
            request=request,
        )
        html_parts.append(row_html)

        # Summary (OOB)
        summary_html = render_to_string(
            "cart/partials/cart_summary.html",
            {"cart": cart, **ctx},
            request=request,
        )
        html_parts.append(summary_html)

        # Cart badge (OOB)
        from cart.context_processors import cart_counts
        counts = cart_counts(request)
        badge_html = render_to_string(
            "cart/partials/cart_badge.html",
            {"cart_count": counts.get("cart_count")},
        )
        html_parts.append(badge_html)

        response = HttpResponse("\n".join(html_parts))
        response["HX-Trigger"] = json.dumps({
            "show-toast": {"message": "Cart updated!", "type": "success"},
        })
        return response

    messages.success(request, f"{item.product.name} quantity updated.")
    return redirect("cart:cart_detail")


@login_required
def cart_detail(request):

    cart = Cart.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=CartItem.objects.select_related(
                "product__category"
            ),
        )
    ).filter(
        user=request.user,
    ).first()

    ctx = _cart_summary_context(request, cart)

    # Get frequently bought together recommendations based on first cart item
    recommendations = []
    if cart and cart.items.exists():
        first_item = cart.items.first()
        recs = get_frequently_bought_together(first_item.product_id, max_results=6)
        # Filter out items already in cart
        cart_pids = set(cart.items.values_list("product_id", flat=True))
        recommendations = [p for p in recs if p.id not in cart_pids][:4]
    ctx["recommendations"] = recommendations

    return render(request, "cart/cart_detail.html", ctx)


@require_POST
@login_required
def toggle_wishlist(request, product_id):

    product = get_object_or_404(Product, id=product_id, is_available=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(id=product_id).exists():
        wishlist.products.remove(product)
        message = f"{product.name} removed from your wishlist."
        added = False
    else:
        wishlist.products.add(product)
        message = f"{product.name} added to your wishlist."
        added = True

    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        badge_html = _wishlist_badge_html(request)
        response = HttpResponse(badge_html)
        response["HX-Trigger"] = json.dumps({
            "show-toast": {
                "message": f"{'Added to' if added else 'Removed from'} wishlist!",
                "type": "success",
            },
        })
        return response

    messages.success(request, message)
    return redirect(request.META.get("HTTP_REFERER", "products:product_list"))
