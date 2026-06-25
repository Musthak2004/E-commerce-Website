from .models import Cart


def cart_counts(request):

    if not request.user.is_authenticated:
        return {
            "cart_count": None,
            "wishlist_count": None,
        }

    cart = Cart.objects.filter(
        user=request.user
    ).prefetch_related("items").first()

    return {
        "cart_count": cart.items.count() if cart else 0,
        "wishlist_count": None,
    }
