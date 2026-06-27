import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import CreateView, UpdateView
from django.views.generic.base import TemplateView

from .forms import ProfileForm, SignUpForm
from .models import CustomUser, Profile

logger = logging.getLogger(__name__)


class SignUpView(CreateView):

    model = CustomUser

    form_class = SignUpForm

    template_name = "registration/signup.html"

    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("home")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verify_url = self.request.build_absolute_uri(f"/accounts/verify/{uid}/{token}/")
        try:
            send_mail(
                subject="Verify your email — ShopEase",
                message=(
                    f"Hi {user.email},\n\n"
                    f"Please verify your email address by clicking the link below:\n\n"
                    f"{verify_url}\n\n"
                    f"Thank you for joining ShopEase!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.warning("Failed to send verification email to %s: %s", user.email, e)
        return response


class VerifyEmailView(TemplateView):
    template_name = "registration/email_verified.html"

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
            return self.render_to_response({"valid": True, "user": user})
        return self.render_to_response({"valid": False})


class ProfileUpdateView(LoginRequiredMixin, UpdateView):

    model = Profile

    form_class = ProfileForm

    template_name = "accounts/profile_form.html"

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy("home")