from django.test import TestCase
from django.urls import reverse, resolve

from .views import HomePageView


class PageURLTests(TestCase):
    def test_home_url_resolves(self):
        resolver = resolve("/")
        self.assertEqual(resolver.func.view_class, HomePageView)

    def test_home_url_name(self):
        url = reverse("home")
        self.assertEqual(url, "/")


class HomeViewTests(TestCase):
    def test_homepage_status_code(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_homepage_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home.html")
