import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from products.models import Product

from .forms import ContactForm
from .models import NewsletterSubscriber

logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Show the 4 newest available products
        context["new_arrivals"] = (
            Product.objects
            .filter(is_available=True)
            .select_related("seller", "category")
            .order_by("-created_at")[:4]
        )
        return context


class ContactPageView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = "/contact/"

    def form_valid(self, form):
        form.save()
        try:
            send_mail(
                subject=f"Contact Form: {form.cleaned_data['subject']}",
                message=(
                    f"From: {form.cleaned_data['name']} ({form.cleaned_data['email']})\n\n"
                    f"{form.cleaned_data['message']}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
        except Exception as e:
            logger.warning("Failed to send contact form email: %s", e)
        messages.success(self.request, "Thank you! Your message has been sent.")
        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class AboutPageView(TemplateView):
    template_name = "about.html"


@require_POST
def newsletter_signup(request):
    email = request.POST.get("email", "").strip()
    if not email:
        messages.error(request, "Please enter a valid email address.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Please enter a valid email address.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    NewsletterSubscriber.objects.get_or_create(email=email)
    messages.success(request, "Thanks for subscribing to our newsletter!")
    return redirect(request.META.get("HTTP_REFERER", "/"))
