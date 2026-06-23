from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import SignUpForm
from .models import CustomUser


class SignUpView(CreateView):

    model = CustomUser

    form_class = SignUpForm

    template_name = "registration/signup.html"

    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("home")

        return super().dispatch(request, *args, **kwargs)