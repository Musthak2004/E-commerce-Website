from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import ProfileForm, SignUpForm
from .models import CustomUser, Profile


class SignUpView(CreateView):

    model = CustomUser

    form_class = SignUpForm

    template_name = "registration/signup.html"

    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("home")

        return super().dispatch(request, *args, **kwargs)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):

    model = Profile

    form_class = ProfileForm

    template_name = "accounts/profile_form.html"

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy("home")