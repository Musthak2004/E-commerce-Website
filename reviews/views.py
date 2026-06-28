from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
)

from products.models import Product

from .forms import ReviewForm
from .models import Review


class ReviewCreateView(
    LoginRequiredMixin,
    CreateView
):

    model = Review

    form_class = ReviewForm

    template_name = "reviews/review_form.html"

    def get_product(self):
        return get_object_or_404(
            Product,
            pk=self.kwargs["product_id"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = self.get_product()
        return context

    def form_valid(self, form):
        product = self.get_product()

        if Review.objects.filter(
            user=self.request.user,
            product=product,
        ).exists():
            messages.error(
                self.request,
                "You have already reviewed this product."
            )
            form.add_error(None, "You have already reviewed this product.")
            return self.form_invalid(form)

        form.instance.user = self.request.user
        form.instance.product = product

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "reviews:review_detail",
            kwargs={"pk": self.object.pk}
        )


class ReviewDetailView(DetailView):

    model = Review

    template_name = "reviews/review_detail.html"

    context_object_name = "review"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "user", "product"
        )