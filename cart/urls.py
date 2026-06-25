from django.urls import path

from .views import (
    add_to_cart,
    remove_from_cart,
    update_quantity,
    cart_detail,
)

app_name = "cart"

urlpatterns = [

    path(
        "",
        cart_detail,
        name="cart_detail"
    ),

    path(
        "add/<int:product_id>/",
        add_to_cart,
        name="add_to_cart"
    ),

    path(
        "remove/<int:item_id>/",
        remove_from_cart,
        name="remove_from_cart"
    ),

    path(
        "update/<int:item_id>/",
        update_quantity,
        name="update_quantity"
    ),
]