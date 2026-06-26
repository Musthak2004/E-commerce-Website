from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
)

from orders.models import Order

from .forms import PaymentForm
from .models import Payment


class PaymentCreateView(
    LoginRequiredMixin,
    CreateView
):

    model = Payment

    form_class = PaymentForm

    template_name = "payments/payment_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        order = get_object_or_404(
            Order,
            pk=self.kwargs["order_id"],
            user=self.request.user,
        )
        kwargs["order"] = order
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = get_object_or_404(
            Order,
            pk=self.kwargs["order_id"],
            user=self.request.user,
        )
        return context

    def form_valid(self, form):
        order = get_object_or_404(
            Order,
            pk=self.kwargs["order_id"],
            user=self.request.user,
        )

        if order.status not in ("PENDING", "CONFIRMED"):
            messages.error(self.request, "This order is not available for payment.")
            return self.form_invalid(form)

        if hasattr(order, "payment"):
            messages.error(self.request, "This order already has a payment record.")
            return self.form_invalid(form)

        form.instance.order = order
        form.instance.amount = order.total_price

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "payments:payment_detail",
            kwargs={"pk": self.object.pk}
        )


class PaymentDetailView(
    LoginRequiredMixin,
    DetailView
):

    model = Payment

    template_name = "payments/payment_detail.html"

    context_object_name = "payment"

    def get_queryset(self):
        return super().get_queryset().filter(
            order__user=self.request.user
        )

