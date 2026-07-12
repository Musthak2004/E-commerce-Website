from django.urls import path

from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)
from .seller_dashboard import seller_dashboard

app_name = "products"

urlpatterns = [

    path("", ProductListView.as_view(), name="product_list"),

    path("dashboard/", seller_dashboard, name="seller_dashboard"),

    path("create/", ProductCreateView.as_view(), name="product_create"),

    path("<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),

    path("<slug:slug>/update/", ProductUpdateView.as_view(), name="product_update"),

    path("<slug:slug>/delete/", ProductDeleteView.as_view(), name="product_delete"),
]