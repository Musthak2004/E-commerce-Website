from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import SignUpForm
from .models import CustomUser


class SignUpView(CreateView):

    model = CustomUser

    form_class = SignUpForm

    template_name = "registration/signup.html"

    success_url = reverse_lazy("login")