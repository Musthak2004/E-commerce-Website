from decimal import Decimal
from unittest.mock import patch

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve

from orders.models import Order
from payments.forms import PaymentForm
from payments.models import Payment
from payments.views import payment_create, payment_success, stripe_webhook, PaymentDetailView

User = get_user_model()


class PaymentModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="pay_model_cust",
            email="pay_model_cust@example.com",
            password="pass123",
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=Decimal("50.00"),
        )

    def test_create_payment(self):
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            payment_method="CARD",
            transaction_id="TXN-001",
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.amount, Decimal("50.00"))
        self.assertEqual(payment.payment_method, "CARD")
        self.assertEqual(payment.transaction_id, "TXN-001")
        self.assertEqual(payment.status, "PENDING")
        self.assertIsNotNone(payment.created_at)
        self.assertIsNotNone(payment.updated_at)

    def test_payment_str(self):
        payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("50.00"),
            payment_method="PAYPAL",
        )
        expected = f"Payment #{payment.id} — Order #{self.order.id} (Pending)"
        self.assertEqual(str(payment), expected)

    def test_payment_ordering(self):
        order2 = Order.objects.create(user=self.user, total_price=Decimal("30.00"))
        p1 = Payment.objects.create(order=self.order, amount=Decimal("50.00"), payment_method="CARD")
        p2 = Payment.objects.create(order=order2, amount=Decimal("30.00"), payment_method="PAYPAL")
        self.assertQuerySetEqual(
            Payment.objects.all(),
            [p2, p1],
        )

    def test_transaction_id_blank_converted_to_null(self):
        payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("50.00"),
            payment_method="CARD",
            transaction_id="",
        )
        payment.refresh_from_db()
        self.assertIsNone(payment.transaction_id)

    def test_one_to_one_uniqueness(self):
        Payment.objects.create(order=self.order, amount=Decimal("50.00"), payment_method="CARD")
        with self.assertRaises(Exception):
            Payment.objects.create(order=self.order, amount=Decimal("50.00"), payment_method="PAYPAL")

    def test_cascade_on_order_delete(self):
        Payment.objects.create(order=self.order, amount=Decimal("50.00"), payment_method="CARD")
        order_id = self.order.id
        self.order.delete()
        self.assertFalse(Payment.objects.filter(order_id=order_id).exists())


class PaymentFormTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="pay_form_cust",
            email="pay_form_cust@example.com",
            password="pass123",
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=Decimal("50.00"),
        )

    def test_form_has_payment_method_field(self):
        form = PaymentForm(order=self.order)
        self.assertIn("payment_method", form.fields)

    def test_valid_form(self):
        form = PaymentForm(order=self.order, data={"payment_method": "CARD"})
        self.assertTrue(form.is_valid())

    def test_zero_value_order_raises_error(self):
        zero_order = Order.objects.create(user=self.user, total_price=Decimal("0.00"))
        form = PaymentForm(order=zero_order, data={"payment_method": "CARD"})
        self.assertFalse(form.is_valid())
        self.assertIn("Cannot process payment for a zero-value order.", form.errors.get("payment_method", []))

    def test_duplicate_payment_raises_error(self):
        Payment.objects.create(order=self.order, amount=Decimal("50.00"), payment_method="CARD")
        form = PaymentForm(order=self.order, data={"payment_method": "PAYPAL"})
        self.assertFalse(form.is_valid())
        self.assertIn("already has a payment record", str(form.errors.get("payment_method", "")))

    def test_form_help_text_with_order(self):
        form = PaymentForm(order=self.order)
        self.assertIn("Total amount:", form.fields["payment_method"].help_text)


class PaymentCreateViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="pay_create_cust",
            email="pay_create_cust@example.com",
            password="pass123",
        )
        self.other_user = User.objects.create_user(
            username="pay_create_other",
            email="pay_create_other@example.com",
            password="pass123",
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=Decimal("50.00"),
        )

    def test_redirects_anonymous(self):
        url = reverse("payments:payment_create", args=[self.order.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, f"/accounts/login/?next={url}")

    def test_other_user_order_returns_404(self):
        self.client.login(username="pay_create_other@example.com", password="pass123")
        url = reverse("payments:payment_create", args=[self.order.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_order_returns_404(self):
        self.client.login(username="pay_create_cust@example.com", password="pass123")
        url = reverse("payments:payment_create", args=[9999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_redirects_to_stripe_checkout(self):
        self.client.login(username="pay_create_cust@example.com", password="pass123")
        url = reverse("payments:payment_create", args=[self.order.id])
        with patch("stripe.checkout.Session.create") as mock_session:
            mock_session.return_value.id = "cs_test_123"
            mock_session.return_value.url = "https://checkout.stripe.com/test"
            resp = self.client.get(url, follow=False)
            self.assertEqual(resp.status_code, 302)
            self.assertTrue(resp.url.startswith("https://checkout.stripe.com/"))

    def test_creates_payment_record(self):
        self.client.login(username="pay_create_cust@example.com", password="pass123")
        url = reverse("payments:payment_create", args=[self.order.id])
        with patch("stripe.checkout.Session.create") as mock_session:
            mock_session.return_value.id = "cs_test_456"
            mock_session.return_value.url = "https://checkout.stripe.com/test"
            self.client.get(url)
            self.assertTrue(Payment.objects.filter(order=self.order).exists())
            payment = Payment.objects.get(order=self.order)
            self.assertEqual(payment.stripe_session_id, "cs_test_456")
            self.assertEqual(payment.status, "PENDING")

    def test_duplicate_payment_redirects(self):
        Payment.objects.create(
            order=self.order,
            amount=Decimal("50.00"),
            payment_method="CARD",
            status="COMPLETED",
        )
        self.client.login(username="pay_create_cust@example.com", password="pass123")
        url = reverse("payments:payment_create", args=[self.order.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("payments:payment_detail", args=[self.order.payment.pk]))

    def test_completed_order_redirects_with_message(self):
        self.order.status = "DELIVERED"
        self.order.save()
        self.client.login(username="pay_create_cust@example.com", password="pass123")
        url = reverse("payments:payment_create", args=[self.order.id])
        resp = self.client.get(url, follow=True)
        self.assertRedirects(resp, reverse("orders:order_detail", args=[self.order.id]))

    def test_non_pending_order_redirects(self):
        self.order.status = "CANCELLED"
        self.order.save()
        self.client.login(username="pay_create_cust@example.com", password="pass123")
        url = reverse("payments:payment_create", args=[self.order.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("orders:order_detail", args=[self.order.id]))


class PaymentSuccessViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pay_succ_cust", email="pay_succ_cust@example.com", password="pass123"
        )
        self.order = Order.objects.create(user=self.user, total_price=Decimal("50.00"))

    def test_success_redirects_anonymous(self):
        url = reverse("payments:payment_success", args=[self.order.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, f"/accounts/login/?next={url}")

    def test_success_no_payment_redirects(self):
        self.client.login(username="pay_succ_cust@example.com", password="pass123")
        url = reverse("payments:payment_success", args=[self.order.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("orders:order_detail", args=[self.order.id]))

    def test_success_with_completed_payment(self):
        Payment.objects.create(
            order=self.order, amount=Decimal("50.00"),
            payment_method="CARD", status="COMPLETED",
            transaction_id="txn_test",
        )
        self.client.login(username="pay_succ_cust@example.com", password="pass123")
        url = reverse("payments:payment_success", args=[self.order.id])
        with patch("stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_session = type("Session", (), {"payment_status": "paid", "payment_intent": "pi_test"})()
            mock_retrieve.return_value = mock_session
            resp = self.client.get(url)
            self.assertRedirects(resp, reverse("payments:payment_detail", args=[self.order.payment.pk]))

    def test_success_with_pending_stripe_session(self):
        payment = Payment.objects.create(
            order=self.order, amount=Decimal("50.00"),
            payment_method="CARD", status="PENDING",
            stripe_session_id="cs_test_123",
        )
        self.client.login(username="pay_succ_cust@example.com", password="pass123")
        url = reverse("payments:payment_success", args=[self.order.id])
        with patch("stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_session = type("Session", (), {"payment_status": "paid", "payment_intent": "pi_test"})()
            mock_retrieve.return_value = mock_session
            resp = self.client.get(url)
            payment.refresh_from_db()
            self.assertEqual(payment.status, "COMPLETED")
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, "CONFIRMED")

    def test_success_stripe_error_handled(self):
        Payment.objects.create(
            order=self.order, amount=Decimal("50.00"),
            payment_method="CARD", status="PENDING",
            stripe_session_id="cs_test_bad",
        )
        self.client.login(username="pay_succ_cust@example.com", password="pass123")
        url = reverse("payments:payment_success", args=[self.order.id])
        with patch("stripe.checkout.Session.retrieve", side_effect=stripe.error.StripeError("err")):
            resp = self.client.get(url)
            self.assertRedirects(resp, reverse("payments:payment_detail", args=[self.order.payment.pk]))


class PaymentURLTests(TestCase):
    def test_payment_create_url_resolves(self):
        resolver = resolve("/payments/create/1/")
        self.assertEqual(resolver.func, payment_create)

    def test_payment_success_url_resolves(self):
        resolver = resolve("/payments/success/1/")
        self.assertEqual(resolver.func, payment_success)

    def test_payment_detail_url_resolves(self):
        resolver = resolve("/payments/1/")
        self.assertEqual(resolver.func.view_class, PaymentDetailView)

    def test_webhook_url_resolves(self):
        resolver = resolve("/payments/webhook/")
        self.assertEqual(resolver.func, stripe_webhook)


class PaymentDetailViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="pay_detail_cust",
            email="pay_detail_cust@example.com",
            password="pass123",
        )
        self.other_user = User.objects.create_user(
            username="pay_detail_other",
            email="pay_detail_other@example.com",
            password="pass123",
        )
        self.order = Order.objects.create(user=self.user, total_price=Decimal("50.00"))
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("50.00"),
            payment_method="CARD",
        )

    def test_redirects_anonymous(self):
        url = reverse("payments:payment_detail", args=[self.payment.pk])
        resp = self.client.get(url)
        self.assertRedirects(resp, f"/accounts/login/?next={url}")

    def test_other_user_gets_404(self):
        self.client.login(username="pay_detail_other@example.com", password="pass123")
        url = reverse("payments:payment_detail", args=[self.payment.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_owner_can_view(self):
        self.client.login(username="pay_detail_cust@example.com", password="pass123")
        url = reverse("payments:payment_detail", args=[self.payment.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "payments/payment_detail.html")
        self.assertEqual(resp.context["payment"], self.payment)

    def test_nonexistent_payment_returns_404(self):
        self.client.login(username="pay_detail_cust@example.com", password="pass123")
        url = reverse("payments:payment_detail", args=[9999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
