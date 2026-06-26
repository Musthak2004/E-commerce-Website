from django.urls import path

from .views import (
    PaymentCreateView,
    PaymentDetailView,
)

app_name = "payments"

urlpatterns = [

    path(
        "create/<int:order_id>/",
        PaymentCreateView.as_view(),
        name="payment_create"
    ),

    path(
        "<int:pk>/",
        PaymentDetailView.as_view(),
        name="payment_detail"
    ),
]