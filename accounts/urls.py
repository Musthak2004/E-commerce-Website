from django.urls import path
from .views import ProfileUpdateView, SignUpView, VerifyEmailView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    path("verify/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify_email"),
]