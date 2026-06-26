from django.urls import path

from .views import (
    ReviewCreateView,
    ReviewDetailView,
)

app_name = "reviews"

urlpatterns = [

    path(
        "create/<int:product_id>/",
        ReviewCreateView.as_view(),
        name="review_create"
    ),

    path(
        "<int:pk>/",
        ReviewDetailView.as_view(),
        name="review_detail"
    ),
]