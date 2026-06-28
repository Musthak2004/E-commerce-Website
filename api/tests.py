from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product

User = get_user_model()


class ProductAPITests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="api_seller", email="api_seller@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat = Category.objects.create(name="API Cat", slug="api-cat")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="API Product", slug="api-product",
            price=25.00, stock=10, is_available=True,
        )
        self.unavailable = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Hidden", slug="hidden",
            price=10, stock=0, is_available=False,
        )

    def test_product_list_returns_200(self):
        url = reverse("product-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_product_list_only_shows_available(self):
        url = reverse("product-list")
        resp = self.client.get(url)
        slugs = [p["slug"] for p in resp.data["results"]]
        self.assertIn("api-product", slugs)
        self.assertNotIn("hidden", slugs)

    def test_product_list_pagination(self):
        url = reverse("product-list")
        resp = self.client.get(url)
        self.assertIn("count", resp.data)
        self.assertIn("results", resp.data)
        self.assertEqual(resp.data["count"], 1)

    def test_product_list_page_size_param(self):
        url = reverse("product-list")
        resp = self.client.get(url, {"page_size": 48})
        self.assertEqual(resp.status_code, 200)

    def test_product_retrieve_by_slug(self):
        url = reverse("product-detail", args=["api-product"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "API Product")
        self.assertEqual(resp.data["slug"], "api-product")

    def test_product_retrieve_unavailable_returns_404(self):
        url = reverse("product-detail", args=["hidden"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_product_retrieve_nonexistent_returns_404(self):
        url = reverse("product-detail", args=["no-such-product"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_product_list_contains_nested_category(self):
        url = reverse("product-list")
        resp = self.client.get(url)
        result = resp.data["results"][0]
        self.assertIn("category", result)
        self.assertEqual(result["category"]["name"], "API Cat")

    def test_product_list_contains_rating_fields(self):
        url = reverse("product-list")
        resp = self.client.get(url)
        result = resp.data["results"][0]
        self.assertIn("average_rating", result)
        self.assertIn("review_count", result)

    def test_product_detail_contains_all_fields(self):
        url = reverse("product-detail", args=["api-product"])
        resp = self.client.get(url)
        expected = {"id", "name", "slug", "description", "price", "stock",
                    "is_available", "image", "category", "tags",
                    "average_rating", "review_count", "created_at"}
        self.assertEqual(set(resp.data.keys()), expected)


class ProductAPIAuthTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="api_auth_seller", email="api_auth_seller@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat = Category.objects.create(name="Auth", slug="auth")
        Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Auth Product", slug="auth-product",
            price=15, stock=5, is_available=True,
        )

    def test_anonymous_can_list(self):
        resp = self.client.get(reverse("product-list"))
        self.assertEqual(resp.status_code, 200)

    def test_anonymous_can_retrieve(self):
        resp = self.client.get(reverse("product-detail", args=["auth-product"]))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_list(self):
        self.client.login(username="api_auth_seller@example.com", password="pass123")
        resp = self.client.get(reverse("product-list"))
        self.assertEqual(resp.status_code, 200)
