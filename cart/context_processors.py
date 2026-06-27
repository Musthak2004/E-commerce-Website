from .models import Cart, Wishlist


def cart_counts(request):

    if not request.user.is_authenticated:
        return {
            "cart_count": None,
            "wishlist_count": None,
        }

    cart = Cart.objects.filter(
        user=request.user
    ).first()

    wishlist_count = 0
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_count = wishlist.products.count()
    except Wishlist.DoesNotExist:
        pass

    return {
        "cart_count": cart.items.count() if cart else 0,
        "wishlist_count": wishlist_count,
    }
