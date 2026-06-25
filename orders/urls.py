from django.urls import path

from .views import (
    create_order,
    order_detail,
    order_list,
)

app_name = "orders"

urlpatterns = [

    path(
        "create/",
        create_order,
        name="create_order"
    ),

    path(
        "",
        order_list,
        name="order_list"
    ),

    path(
        "<int:order_id>/",
        order_detail,
        name="order_detail"
    ),
]