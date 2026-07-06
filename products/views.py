from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q, Case, IntegerField, Value, When
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

from .models import Category, Product, Tag
from .forms import ProductForm
from .filters import ProductFilter
from .recommendations import (
    get_frequently_bought_together,
    get_related_products,
    track_product_view,
)


class SellerRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == "SELLER"

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied


class ProductListView(ListView):

    model = Product

    template_name = "products/product_list.html"

    context_object_name = "products"

    paginate_by = 12

    def get_queryset(self):

        qs = Product.objects.filter(
            is_available=True
        ).select_related(
            "seller", "category"
        ).prefetch_related(
            "tags"
        )

        # Apply declarative django-filter — replaces hand-rolled filter logic
        self.filter = ProductFilter(self.request.GET, queryset=qs)
        qs = self.filter.qs

        query = self.request.GET.get("q", "").strip()
        if query:
            # Add relevance annotation: name matches rank higher than description matches
            name_match = Q(name__icontains=query)
            qs = qs.annotate(
                relevance=(
                    Case(
                        When(name__icontains=query, then=Value(2)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )
            )
        else:
            qs = qs.annotate(
                relevance=Value(1, output_field=IntegerField())
            )

        sort = self.request.GET.get("sort", "").strip()
        if sort == "price_asc":
            qs = qs.order_by("price")
        elif sort == "price_desc":
            qs = qs.order_by("-price")
        elif sort == "name":
            qs = qs.order_by("name")
        elif sort == "oldest":
            qs = qs.order_by("created_at")
        elif sort == "rating":
            qs = qs.annotate(avg_rating=Avg("reviews__rating")).order_by("-avg_rating")
        else:
            # Default: sort by relevance (search) then newest
            qs = qs.order_by("-relevance", "-created_at")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_params = getattr(self, "filter", None)
        context["filter"] = filter_params
        context["query"] = self.request.GET.get("q", "").strip()
        context["current_category"] = self.request.GET.get("category", "").strip()
        context["current_tag"] = self.request.GET.get("tag", "").strip()
        context["current_sort"] = self.request.GET.get("sort", "").strip()
        context["min_price"] = self.request.GET.get("min_price", "").strip()
        context["max_price"] = self.request.GET.get("max_price", "").strip()
        context["min_rating"] = self.request.GET.get("min_rating", "").strip()
        context["categories"] = Category.objects.filter(
            products__is_available=True
        ).distinct()
        context["tags"] = Tag.objects.filter(
            products__is_available=True
        ).distinct()
        return context


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

        # Track this view for Recently Viewed recommendations
        track_product_view(self.request, product)

        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context["extra_images"] = product.images.all()

        # --- Recommendations ---
        # 1. Enhanced related products (category/tag based, ordered by rating + sales)
        context["related_products"] = get_related_products(product)

        # 2. Frequently bought together (co-occurrence in orders)
        context["bought_together"] = get_frequently_bought_together(product)

        return context


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