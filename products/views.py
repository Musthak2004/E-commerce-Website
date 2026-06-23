from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.urls import reverse_lazy

from django.shortcuts import get_object_or_404

from .models import Product
from .forms import ProductForm


class SellerRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == "SELLER"


class ProductListView(ListView):

    model = Product

    template_name = "products/product_list.html"

    context_object_name = "products"

    paginate_by = 12

    def get_queryset(self):

        return Product.objects.filter(
            is_available=True
        ).select_related(
            "seller", "category"
        )


class ProductDetailView(DetailView):

    model = Product

    template_name = "products/product_detail.html"

    context_object_name = "product"

    def get_object(self):

        product = get_object_or_404(
            Product,
            slug=self.kwargs.get("slug"),
            is_available=True,
        )

        return product


class ProductCreateView(
    LoginRequiredMixin,
    SellerRequiredMixin,
    CreateView
):

    model = Product

    form_class = ProductForm

    template_name = "products/product_form.html"

    success_url = reverse_lazy("products:product_list")

    def form_valid(self, form):

        form.instance.seller = self.request.user

        return super().form_valid(form)


class ProductUpdateView(
    LoginRequiredMixin,
    SellerRequiredMixin,
    UpdateView
):

    model = Product

    form_class = ProductForm

    template_name = "products/product_form.html"

    success_url = reverse_lazy("products:product_list")

    def get_queryset(self):

        return Product.objects.filter(
            seller=self.request.user
        )


class ProductDeleteView(
    LoginRequiredMixin,
    SellerRequiredMixin,
    DeleteView
):

    model = Product

    template_name = "products/product_confirm_delete.html"

    success_url = reverse_lazy("products:product_list")

    def get_queryset(self):

        return Product.objects.filter(
            seller=self.request.user
        )