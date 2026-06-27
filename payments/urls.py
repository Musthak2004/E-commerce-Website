from django.urls import path

from .views import (
    PaymentDetailView,
    payment_create,
    payment_success,
    stripe_webhook,
)

app_name = "payments"

urlpatterns = [
    path(
        "create/<int:order_id>/",
        payment_create,
        name="payment_create"
    ),
    path(
        "success/<int:order_id>/",
        payment_success,
        name="payment_success"
    ),
    path(
        "<int:pk>/",
        PaymentDetailView.as_view(),
        name="payment_detail"
    ),
    path(
        "webhook/",
        stripe_webhook,
        name="stripe_webhook"
    ),
]
