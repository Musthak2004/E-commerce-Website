from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve
from django.utils import timezone

from coupons.forms import CouponApplyForm
from coupons.models import Coupon
from coupons.views import apply_coupon, remove_coupon

User = get_user_model()


class CouponModelTests(TestCase):

    def setUp(self):
        self.now = timezone.now()

    def test_create_coupon(self):
        coupon = Coupon.objects.create(
            code="SAVE10",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(coupon.code, "SAVE10")
        self.assertEqual(coupon.discount_type, "PERCENTAGE")
        self.assertEqual(coupon.discount_value, 10)
        self.assertEqual(coupon.usage_limit, 1)
        self.assertEqual(coupon.used_count, 0)
        self.assertTrue(coupon.is_active)
        self.assertIsNotNone(coupon.created_at)

    def test_coupon_str(self):
        coupon = Coupon.objects.create(
            code="FLAT5",
            discount_type="FIXED",
            discount_value=5,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(str(coupon), "FLAT5")

    def test_coupon_ordering(self):
        c1 = Coupon.objects.create(
            code="C1", discount_type="PERCENTAGE", discount_value=10,
            valid_from=self.now, valid_to=self.now + timedelta(days=30),
        )
        c2 = Coupon.objects.create(
            code="C2", discount_type="FIXED", discount_value=5,
            valid_from=self.now, valid_to=self.now + timedelta(days=30),
        )
        self.assertQuerySetEqual(Coupon.objects.all(), [c2, c1])

    def test_is_valid_active_within_range(self):
        coupon = Coupon.objects.create(
            code="VALID1",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=30),
            is_active=True,
        )
        self.assertTrue(coupon.is_valid)

    def test_is_valid_inactive(self):
        coupon = Coupon.objects.create(
            code="INACTIVE",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=30),
            is_active=False,
        )
        self.assertFalse(coupon.is_valid)

    def test_is_valid_expired(self):
        coupon = Coupon.objects.create(
            code="EXPIRED",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=self.now - timedelta(days=60),
            valid_to=self.now - timedelta(days=1),
        )
        self.assertFalse(coupon.is_valid)

    def test_is_valid_future(self):
        coupon = Coupon.objects.create(
            code="FUTURE",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=self.now + timedelta(days=1),
            valid_to=self.now + timedelta(days=30),
        )
        self.assertFalse(coupon.is_valid)

    def test_is_valid_usage_limit_reached(self):
        coupon = Coupon.objects.create(
            code="USEDUP",
            discount_type="FIXED",
            discount_value=5,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=30),
            usage_limit=1,
            used_count=1,
        )
        self.assertFalse(coupon.is_valid)

    def test_unique_code(self):
        Coupon.objects.create(
            code="UNIQUE",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=self.now, valid_to=self.now + timedelta(days=30),
        )
        with self.assertRaises(Exception):
            Coupon.objects.create(
                code="UNIQUE",
                discount_type="FIXED",
                discount_value=5,
                valid_from=self.now, valid_to=self.now + timedelta(days=30),
            )

    def test_percentage_cannot_exceed_100(self):
        coupon = Coupon(
            code="OVR100",
            discount_type="PERCENTAGE",
            discount_value=150,
            valid_from=self.now, valid_to=self.now + timedelta(days=30),
        )
        with self.assertRaises(Exception):
            coupon.save()

    def test_valid_from_before_valid_to_required(self):
        coupon = Coupon(
            code="BADDATE",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=self.now + timedelta(days=1),
            valid_to=self.now - timedelta(days=1),
        )
        with self.assertRaises(Exception):
            coupon.save()

    def test_get_discount_percentage(self):
        coupon = Coupon.objects.create(
            code="PCT20", discount_type="PERCENTAGE", discount_value=20,
            valid_from=self.now - timedelta(days=1), valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(coupon.get_discount(Decimal("100.00")), Decimal("20.00"))

    def test_get_discount_fixed(self):
        coupon = Coupon.objects.create(
            code="FIXED5", discount_type="FIXED", discount_value=5,
            valid_from=self.now - timedelta(days=1), valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(coupon.get_discount(Decimal("100.00")), Decimal("5.00"))

    def test_get_discount_percentage_with_max(self):
        coupon = Coupon.objects.create(
            code="PCT50MAX30", discount_type="PERCENTAGE", discount_value=50,
            maximum_discount=30,
            valid_from=self.now - timedelta(days=1), valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(coupon.get_discount(Decimal("100.00")), Decimal("30.00"))

    def test_get_discount_fixed_does_not_exceed_total(self):
        coupon = Coupon.objects.create(
            code="FIXED10", discount_type="FIXED", discount_value=10,
            valid_from=self.now - timedelta(days=1), valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(coupon.get_discount(Decimal("5.00")), Decimal("5.00"))

    def test_get_discount_below_minimum(self):
        coupon = Coupon.objects.create(
            code="MIN50", discount_type="PERCENTAGE", discount_value=20,
            minimum_order_amount=50,
            valid_from=self.now - timedelta(days=1), valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(coupon.get_discount(Decimal("30.00")), Decimal("0.00"))

    def test_get_discount_percentage_over_100_capped(self):
        coupon = Coupon.objects.create(
            code="PCT100", discount_type="PERCENTAGE", discount_value=100,
            valid_from=self.now - timedelta(days=1), valid_to=self.now + timedelta(days=30),
        )
        self.assertEqual(coupon.get_discount(Decimal("100.00")), Decimal("100.00"))


class CouponApplyFormTests(TestCase):

    def test_form_has_code_field(self):
        form = CouponApplyForm()
        self.assertIn("code", form.fields)

    def test_code_normalized_to_uppercase(self):
        form = CouponApplyForm(data={"code": "  save20  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["code"], "SAVE20")

    def test_empty_code_invalid(self):
        form = CouponApplyForm(data={"code": ""})
        self.assertFalse(form.is_valid())


class CouponURLTests(TestCase):
    def test_apply_coupon_url_resolves(self):
        resolver = resolve("/coupons/apply/")
        self.assertEqual(resolver.func, apply_coupon)

    def test_remove_coupon_url_resolves(self):
        resolver = resolve("/coupons/remove/")
        self.assertEqual(resolver.func, remove_coupon)


class ApplyCouponViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="coupon_cust",
            email="coupon_cust@example.com",
            password="pass123",
        )
        self.now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="SAVE20",
            discount_type="PERCENTAGE",
            discount_value=20,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=30),
        )

    def test_redirects_anonymous(self):
        url = reverse("coupons:apply_coupon")
        resp = self.client.post(url, {"code": "SAVE20"})
        self.assertRedirects(resp, f"/accounts/login/?next={url}")

    def test_get_returns_405(self):
        self.client.login(username="coupon_cust@example.com", password="pass123")
        url = reverse("coupons:apply_coupon")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_valid_coupon_stores_in_session(self):
        self.client.login(username="coupon_cust@example.com", password="pass123")
        url = reverse("coupons:apply_coupon")
        resp = self.client.post(url, {"code": "SAVE20"}, follow=True)
        self.assertEqual(self.client.session.get("coupon_id"), self.coupon.id)

    def test_valid_coupon_case_insensitive(self):
        self.client.login(username="coupon_cust@example.com", password="pass123")
        url = reverse("coupons:apply_coupon")
        resp = self.client.post(url, {"code": "  save20  "}, follow=True)
        self.assertEqual(self.client.session.get("coupon_id"), self.coupon.id)

    def test_expired_coupon_shows_error(self):
        expired = Coupon.objects.create(
            code="EXPIRED",
            discount_type="FIXED",
            discount_value=5,
            valid_from=self.now - timedelta(days=60),
            valid_to=self.now - timedelta(days=1),
        )
        self.client.login(username="coupon_cust@example.com", password="pass123")
        url = reverse("coupons:apply_coupon")
        resp = self.client.post(url, {"code": "EXPIRED"}, follow=True)
        self.assertNotIn("coupon_id", self.client.session)
        messages = list(resp.context["messages"])
        self.assertTrue(any("invalid or expired" in str(m) for m in messages))

    def test_nonexistent_coupon_shows_error(self):
        self.client.login(username="coupon_cust@example.com", password="pass123")
        url = reverse("coupons:apply_coupon")
        resp = self.client.post(url, {"code": "NONEXISTENT"}, follow=True)
        self.assertNotIn("coupon_id", self.client.session)
        messages = list(resp.context["messages"])
        self.assertTrue(any("not found" in str(m) for m in messages))

    def test_redirects_to_cart(self):
        self.client.login(username="coupon_cust@example.com", password="pass123")
        url = reverse("coupons:apply_coupon")
        resp = self.client.post(url, {"code": "SAVE20"})
        self.assertRedirects(resp, reverse("cart:cart_detail"))


class RemoveCouponViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="remove_coupon_cust",
            email="remove_coupon_cust@example.com",
            password="pass123",
        )

    def test_redirects_anonymous(self):
        url = reverse("coupons:remove_coupon")
        resp = self.client.post(url)
        self.assertRedirects(resp, f"/accounts/login/?next={url}")

    def test_get_returns_405(self):
        self.client.login(username="remove_coupon_cust@example.com", password="pass123")
        url = reverse("coupons:remove_coupon")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_removes_coupon_from_session(self):
        self.client.login(username="remove_coupon_cust@example.com", password="pass123")
        session = self.client.session
        session["coupon_id"] = 1
        session.save()
        url = reverse("coupons:remove_coupon")
        self.client.post(url, follow=True)
        self.assertNotIn("coupon_id", self.client.session)

    def test_remove_when_no_coupon_in_session(self):
        self.client.login(username="remove_coupon_cust@example.com", password="pass123")
        url = reverse("coupons:remove_coupon")
        resp = self.client.post(url, follow=True)
        self.assertRedirects(resp, reverse("cart:cart_detail"))
