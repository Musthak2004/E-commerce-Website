from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from orders.models import OrderItem
from products.models import Product


@login_required
def seller_dashboard(request):
    """Dashboard view for sellers showing their products, orders, and stats."""

    if request.user.user_type != "SELLER":
        from django.contrib import messages
        messages.error(request, "You need a seller account to access the dashboard.")
        from django.shortcuts import redirect
        return redirect("home")

    # Seller's products
    products = Product.objects.filter(seller=request.user).select_related("category")

    # Orders containing seller's products
    seller_order_items = OrderItem.objects.filter(
        product__seller=request.user
    ).select_related("order", "product")

    total_orders = seller_order_items.values("order").distinct().count()
    total_items_sold = seller_order_items.aggregate(total=Sum("quantity"))["total"] or 0

    from django.db.models import F, Value, DecimalField
    from django.db.models.functions import Coalesce

    revenue = seller_order_items.filter(
        order__status__in=["CONFIRMED", "SHIPPED", "DELIVERED"]
    ).annotate(
        item_revenue=F("price") * F("quantity")
    ).aggregate(
        total=Coalesce(Sum("item_revenue"), Value(0), output_field=DecimalField())
    )["total"]

    context = {
        "products": products,
        "total_products": products.count(),
        "total_orders": total_orders,
        "total_items_sold": total_items_sold,
        "total_revenue": revenue,
        "title": "Seller Dashboard",
    }
    return render(request, "products/seller_dashboard.html", context)
