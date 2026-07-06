from django import template

from products.recommendations import (
    get_frequently_bought_together,
    get_recently_viewed,
)

register = template.Library()


@register.inclusion_tag("products/includes/recommended_products.html", takes_context=True)
def recently_viewed_products(context, max_results=6):
    """Renders a product grid of recently-viewed products for the current user.

    Usage: {% recently_viewed_products [max_results] %}
    """
    request = context["request"]
    products = get_recently_viewed(request, max_results=max_results)
    return {"products": products, "title": "Recently Viewed", "subtitle": "Pick up where you left off."}


@register.inclusion_tag("products/includes/recommended_products.html", takes_context=False)
def frequently_bought_together(product, max_results=4):
    """Renders a product grid of products frequently bought with *product*.

    Usage: {% frequently_bought_together product [max_results] %}
    """
    products = get_frequently_bought_together(product, max_results=max_results)
    return {"products": products, "title": "Frequently Bought Together", "subtitle": "Customers who bought this also purchased."}
