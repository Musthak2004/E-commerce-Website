from django.urls import path
from .views import AboutPageView, ContactPageView, HomePageView, newsletter_signup

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("contact/", ContactPageView.as_view(), name="contact"),
    path("about/", AboutPageView.as_view(), name="about"),
    path("newsletter/", newsletter_signup, name="newsletter_signup"),
]
