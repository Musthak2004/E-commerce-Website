from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product
from reviews.forms import ReviewForm
from reviews.models import Review

User = get_user_model()


class ReviewModelTests(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(
            username="rev_model_seller",
            email="rev_model_seller@example.com",
            password="pass123",
            user_type="SELLER",
        )
        self.user = User.objects.create_user(
            username="rev_model_cust",
            email="rev_model_cust@example.com",
            password="pass123",
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.cat,
            name="Test Product",
            slug="test-product",
            price=25.00,
            stock=10,
        )

    def test_create_review(self):
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=5,
            comment="Great product!",
        )
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great product!")
        self.assertIsNotNone(review.created_at)
        self.assertIsNotNone(review.updated_at)

    def test_review_str(self):
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=4,
            comment="Nice.",
        )
        expected = f"{self.user.email} - {self.product.name} (4★)"
        self.assertEqual(str(review), expected)

    def test_review_ordering(self):
        r1 = Review.objects.create(user=self.user, product=self.product, rating=3)
        product2 = Product.objects.create(
            seller=self.seller, category=self.cat, name="P2", slug="p2", price=10.00, stock=5,
        )
        r2 = Review.objects.create(user=self.user, product=product2, rating=5)
        self.assertQuerySetEqual(
            Review.objects.all(),
            [r2, r1],
        )

    def test_unique_user_product_constraint(self):
        Review.objects.create(user=self.user, product=self.product, rating=5)
        with self.assertRaises(Exception):
            Review.objects.create(user=self.user, product=self.product, rating=3)

    def test_cascade_on_user_delete(self):
        Review.objects.create(user=self.user, product=self.product, rating=5)
        user_id = self.user.id
        self.user.delete()
        self.assertFalse(Review.objects.filter(user_id=user_id).exists())

    def test_cascade_on_product_delete(self):
        Review.objects.create(user=self.user, product=self.product, rating=5)
        product_id = self.product.id
        self.product.delete()
        self.assertFalse(Review.objects.filter(product_id=product_id).exists())

    def test_rating_validators(self):
        review = Review(user=self.user, product=self.product, rating=6)
        with self.assertRaises(ValidationError):
            review.full_clean()
        review2 = Review(user=self.user, product=self.product, rating=0)
        with self.assertRaises(ValidationError):
            review2.full_clean()

    def test_comment_blank_allowed(self):
        review = Review.objects.create(user=self.user, product=self.product, rating=4)
        self.assertEqual(review.comment, "")


class ReviewFormTests(TestCase):

    def test_form_has_rating_and_comment_fields(self):
        form = ReviewForm()
        self.assertIn("rating", form.fields)
        self.assertIn("comment", form.fields)

    def test_valid_form(self):
        form = ReviewForm(data={"rating": 5, "comment": "Excellent product!"})
        self.assertTrue(form.is_valid())

    def test_valid_form_blank_comment(self):
        form = ReviewForm(data={"rating": 4, "comment": ""})
        self.assertTrue(form.is_valid())

    def test_invalid_rating(self):
        form = ReviewForm(data={"rating": 6, "comment": "Good."})
        self.assertFalse(form.is_valid())

    def test_comment_too_short(self):
        form = ReviewForm(data={"rating": 3, "comment": "  Hi  "})
        self.assertFalse(form.is_valid())
        self.assertIn("too short", str(form.errors.get("comment", "")))

    def test_missing_rating(self):
        form = ReviewForm(data={"comment": "Great product!"})
        self.assertFalse(form.is_valid())


class ReviewCreateViewTests(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(
            username="rev_create_seller",
            email="rev_create_seller@example.com",
            password="pass123",
            user_type="SELLER",
        )
        self.user = User.objects.create_user(
            username="rev_create_cust",
            email="rev_create_cust@example.com",
            password="pass123",
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.cat,
            name="Test Product",
            slug="test-product",
            price=25.00,
            stock=10,
        )

    def test_redirects_anonymous(self):
        url = reverse("reviews:review_create", args=[self.product.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, f"/accounts/login/?next={url}")

    def test_get_uses_correct_template(self):
        self.client.login(username="rev_create_cust@example.com", password="pass123")
        url = reverse("reviews:review_create", args=[self.product.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "reviews/review_form.html")

    def test_context_contains_product(self):
        self.client.login(username="rev_create_cust@example.com", password="pass123")
        url = reverse("reviews:review_create", args=[self.product.id])
        resp = self.client.get(url)
        self.assertEqual(resp.context["product"], self.product)

    def test_successful_review_creation(self):
        self.client.login(username="rev_create_cust@example.com", password="pass123")
        url = reverse("reviews:review_create", args=[self.product.id])
        resp = self.client.post(url, {"rating": 5, "comment": "Absolutely amazing product!"})
        self.assertRedirects(resp, reverse("reviews:review_detail", args=[Review.objects.first().pk]))
        self.assertTrue(Review.objects.filter(user=self.user, product=self.product).exists())

    def test_duplicate_review_shows_error(self):
        self.client.login(username="rev_create_cust@example.com", password="pass123")
        url = reverse("reviews:review_create", args=[self.product.id])
        Review.objects.create(user=self.user, product=self.product, rating=5, comment="Great!")
        resp = self.client.post(url, {"rating": 3, "comment": "It was okay I guess."}, follow=True)
        messages = list(resp.context["messages"])
        self.assertTrue(any("already reviewed" in str(m) for m in messages))

    def test_invalid_form_rerenders(self):
        self.client.login(username="rev_create_cust@example.com", password="pass123")
        url = reverse("reviews:review_create", args=[self.product.id])
        resp = self.client.post(url, {"rating": 6, "comment": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "reviews/review_form.html")

    def test_nonexistent_product_returns_404(self):
        self.client.login(username="rev_create_cust@example.com", password="pass123")
        url = reverse("reviews:review_create", args=[9999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


class ReviewDetailViewTests(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(
            username="rev_detail_seller",
            email="rev_detail_seller@example.com",
            password="pass123",
            user_type="SELLER",
        )
        self.user = User.objects.create_user(
            username="rev_detail_cust",
            email="rev_detail_cust@example.com",
            password="pass123",
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.cat,
            name="Test Product",
            slug="test-product",
            price=25.00,
            stock=10,
        )
        self.review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=4,
            comment="Nice product.",
        )

    def test_detail_uses_correct_template(self):
        url = reverse("reviews:review_detail", args=[self.review.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "reviews/review_detail.html")

    def test_context_contains_review(self):
        url = reverse("reviews:review_detail", args=[self.review.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.context["review"], self.review)

    def test_nonexistent_review_returns_404(self):
        url = reverse("reviews:review_detail", args=[9999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
