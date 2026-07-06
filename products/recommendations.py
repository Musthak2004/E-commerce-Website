from django.db.models import Avg, Count, Q

from .models import Product


# ─── Recently Viewed (session-based) ────────────────────────────────────

RECENTLY_VIEWED_SESSION_KEY = "recently_viewed_ids"
MAX_RECENTLY_VIEWED = 12


def track_product_view(request, product):
    """Store a product id in the session's recently-viewed list (deduplicated,
       most-recent-first, capped at MAX_RECENTLY_VIEWED)."""
    viewed = request.session.get(RECENTLY_VIEWED_SESSION_KEY, [])
    # Remove existing entry so we can push it to front
    try:
        viewed.remove(product.pk)
    except ValueError:
        pass
    viewed.insert(0, product.pk)
    request.session[RECENTLY_VIEWED_SESSION_KEY] = viewed[:MAX_RECENTLY_VIEWED]
    # Mark session as modified — Django may not detect list mutation
    request.session.modified = True


def get_recently_viewed(request, max_results=8):
    """Return Product queryset for the recently-viewed ids stored in session,
       maintaining session order."""
    viewed_ids = request.session.get(RECENTLY_VIEWED_SESSION_KEY, [])
    if not viewed_ids:
        return Product.objects.none()

    qs = Product.objects.filter(
        pk__in=viewed_ids[:max_results],
        is_available=True,
    ).select_related("seller", "category")

    # Preserve the order from the session list
    ordered = []
    for pk in viewed_ids:
        for p in qs:
            if p.pk == pk:
                ordered.append(p)
                break
    return ordered


# ─── Frequently Bought Together ────────────────────────────────────────

def get_frequently_bought_together(product, max_results=4):
    """Find products that frequently appear in the same orders as *product*,
       ordered by co-occurrence count descending.

    Uses only non-cancelled orders to keep recommendations relevant.
    """
    from orders.models import OrderItem, Order

    # Get IDs of orders containing this product (exclude cancelled)
    order_ids = OrderItem.objects.filter(
        product=product,
        order__status__in=("PENDING", "CONFIRMED", "SHIPPED", "DELIVERED"),
    ).values_list("order_id", flat=True)

    if not order_ids:
        return Product.objects.none()

    # Find other products in those same orders, ranked by frequency
    paired_ids = (
        OrderItem.objects
        .filter(order_id__in=list(order_ids))
        .exclude(product=product)
        .values("product_id")
        .annotate(score=Count("product_id"))
        .order_by("-score")[:max_results]
        .values_list("product_id", flat=True)
    )

    if not paired_ids:
        return Product.objects.none()

    qs = Product.objects.filter(
        pk__in=list(paired_ids),
        is_available=True,
    ).select_related("seller", "category")

    # Preserve score order
    ordered = []
    for pid in paired_ids:
        for p in qs:
            if p.pk == pid:
                ordered.append(p)
                break
    return ordered


# ─── Enhanced Related Products ─────────────────────────────────────────

def get_related_products(product, max_results=4):
    """Return products related by category *or* shared tags, ordered by
       average rating then sales count (so best-liked and most-bought
       products show first)."""
    return Product.objects.filter(
        is_available=True,
    ).exclude(
        pk=product.pk,
    ).filter(
        Q(category=product.category) | Q(tags__in=product.tags.all()),
    ).distinct().select_related(
        "seller", "category",
    ).annotate(
        avg_rating=Avg("reviews__rating"),
        sales_count=Count("order_items", filter=Q(order_items__order__status__in=(
            "CONFIRMED", "SHIPPED", "DELIVERED",
        ))),
    ).order_by("-avg_rating", "-sales_count")[:max_results]
