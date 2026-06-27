from decimal import Decimal

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model

from products.models import Category, Product
from cart.models import Cart, CartItem
from .models import Order, OrderItem
from .views import create_order, order_detail, order_list
from datetime import timedelta
from django.utils import timezone
from coupons.models import Coupon

User = get_user_model()


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="orderuser",
            email="order@example.com",
            password="pass123"
        )
        self.order = Order.objects.create(user=self.user, total_price=100.00)

    def test_create_order(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.total_price, Decimal("100.00"))
        self.assertEqual(self.order.status, "PENDING")
        self.assertIsNotNone(self.order.created_at)

    def test_order_str(self):
        self.assertEqual(str(self.order), f"Order #{self.order.id} - {self.user.email}")

    def test_order_ordering(self):
        other = Order.objects.create(user=self.user, total_price=50)
        qs = Order.objects.all()
        self.assertEqual(qs.first(), other)

    def test_order_status_choices(self):
        for status_code, _ in Order.STATUS_CHOICES:
            self.order.status = status_code
            self.order.save()
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, status_code)

    def test_order_cascade_delete(self):
        order_id = self.order.id
        self.user.delete()
        self.assertFalse(Order.objects.filter(id=order_id).exists())

    def test_order_verbose_names(self):
        self.assertEqual(Order._meta.verbose_name, "Order")
        self.assertEqual(Order._meta.verbose_name_plural, "Orders")


class OrderItemModelTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Test Product", slug="test-product",
            price=25.00, stock=10
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.order = Order.objects.create(user=self.user, total_price=50.00)
        self.item = OrderItem.objects.create(
            order=self.order, product=self.product,
            quantity=2, price=25.00
        )

    def test_create_order_item(self):
        self.assertEqual(self.item.quantity, 2)
        self.assertEqual(self.item.price, Decimal("25.00"))
        self.assertEqual(self.item.product, self.product)

    def test_order_item_str(self):
        self.assertEqual(str(self.item), self.product.name)

    def test_order_item_total_price(self):
        self.assertEqual(self.item.total_price, Decimal("50.00"))

    def test_order_item_ordering(self):
        p2 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Second", slug="second", price=10, stock=5
        )
        item2 = OrderItem.objects.create(
            order=self.order, product=p2, quantity=1, price=10
        )
        qs = OrderItem.objects.all()
        self.assertEqual(qs[0], self.item)
        self.assertEqual(qs[1], item2)

    def test_order_item_cascade_on_order_delete(self):
        item_id = self.item.id
        self.order.delete()
        self.assertFalse(OrderItem.objects.filter(id=item_id).exists())

    def test_order_item_cascade_on_product_delete(self):
        item_id = self.item.id
        self.product.delete()
        self.assertFalse(OrderItem.objects.filter(id=item_id).exists())

    def test_order_item_verbose_names(self):
        self.assertEqual(OrderItem._meta.verbose_name, "Order Item")
        self.assertEqual(OrderItem._meta.verbose_name_plural, "Order Items")


class OrderURLTests(TestCase):
    def test_create_order_url_resolves(self):
        resolver = resolve("/orders/create/")
        self.assertEqual(resolver.func, create_order)

    def test_create_order_url_name(self):
        url = reverse("orders:create_order")
        self.assertEqual(url, "/orders/create/")

    def test_order_list_url_resolves(self):
        resolver = resolve("/orders/")
        self.assertEqual(resolver.func, order_list)

    def test_order_list_url_name(self):
        url = reverse("orders:order_list")
        self.assertEqual(url, "/orders/")

    def test_order_detail_url_resolves(self):
        resolver = resolve("/orders/1/")
        self.assertEqual(resolver.func, order_detail)

    def test_order_detail_url_name(self):
        url = reverse("orders:order_detail", args=[1])
        self.assertEqual(url, "/orders/1/")


class CreateOrderViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Test Product", slug="test-product",
            price=25.00, stock=10, is_available=True
        )
        self.low_stock_product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Low Stock", slug="low-stock",
            price=15.00, stock=2, is_available=True
        )
        self.unavailable_product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Unavailable", slug="unavailable",
            price=10, stock=0, is_available=False
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_create_order_redirects_anonymous(self):
        resp = self.client.post(reverse("orders:create_order"))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('orders:create_order')}"
        )

    def test_create_order_get_returns_405(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:create_order"))
        self.assertEqual(resp.status_code, 405)

    def test_create_order_empty_cart(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("orders:create_order"))
        self.assertRedirects(resp, reverse("cart:cart_detail"))

    def test_create_order_success(self):
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        resp = self.client.post(reverse("orders:create_order"))
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertRedirects(resp, reverse("orders:order_detail", args=[order.id]))
        self.assertEqual(order.total_price, Decimal("50.00"))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)
        self.assertEqual(order.items.first().quantity, 2)

    def test_create_order_clears_cart(self):
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        self.client.post(reverse("orders:create_order"))
        self.assertEqual(self.cart.items.count(), 0)

    def test_create_order_fails_if_unavailable_product(self):
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.unavailable_product, quantity=1)
        resp = self.client.post(reverse("orders:create_order"))
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.assertEqual(Order.objects.count(), 0)

    def test_create_order_fails_if_insufficient_stock(self):
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.low_stock_product, quantity=5)
        resp = self.client.post(reverse("orders:create_order"))
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.assertEqual(Order.objects.count(), 0)

    def test_create_order_with_multiple_items(self):
        self.client.login(username="cust@example.com", password="pass123")
        p2 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Second", slug="second",
            price=10, stock=20, is_available=True
        )
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        CartItem.objects.create(cart=self.cart, product=p2, quantity=3)
        resp = self.client.post(reverse("orders:create_order"))
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_price, Decimal("55.00"))

    def test_create_order_decrements_stock(self):
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.client.post(reverse("orders:create_order"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_create_order_decrements_stock_for_multiple_items(self):
        self.client.login(username="cust@example.com", password="pass123")
        p2 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Second", slug="second",
            price=10, stock=20, is_available=True
        )
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=self.cart, product=p2, quantity=3)
        self.client.post(reverse("orders:create_order"))
        self.product.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(p2.stock, 17)

    def test_create_order_atomic_stock_check(self):
        self.client.login(username="cust@example.com", password="pass123")
        p2 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Low Stock", slug="low-stock-2",
            price=10, stock=2, is_available=True
        )
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=self.cart, product=p2, quantity=5)
        resp = self.client.post(reverse("orders:create_order"))
        self.product.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(p2.stock, 2)
        self.assertEqual(Order.objects.count(), 0)

    def test_create_order_with_percentage_coupon(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="PCT20",
            discount_type="PERCENTAGE",
            discount_value=20,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
        )
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        session = self.client.session
        session["coupon_id"] = coupon.id
        session.save()
        resp = self.client.post(reverse("orders:create_order"))
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.discount_amount, Decimal("10.00"))
        self.assertEqual(order.total_price, Decimal("40.00"))
        self.assertEqual(order.coupon, coupon)

    def test_create_order_with_fixed_coupon(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="FIXED5",
            discount_type="FIXED",
            discount_value=5,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
        )
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        session = self.client.session
        session["coupon_id"] = coupon.id
        session.save()
        resp = self.client.post(reverse("orders:create_order"))
        order = Order.objects.first()
        self.assertEqual(order.discount_amount, Decimal("5.00"))
        self.assertEqual(order.total_price, Decimal("45.00"))
        self.assertEqual(order.coupon, coupon)

    def test_create_order_coupon_used_count_incremented(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="USEME",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
            usage_limit=10,
            used_count=0,
        )
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        session = self.client.session
        session["coupon_id"] = coupon.id
        session.save()
        self.client.post(reverse("orders:create_order"))
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)

    def test_create_order_coupon_cleared_from_session(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="CLEARME",
            discount_type="PERCENTAGE",
            discount_value=10,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
        )
        self.client.login(username="cust@example.com", password="pass123")
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        session = self.client.session
        session["coupon_id"] = coupon.id
        session.save()
        self.client.post(reverse("orders:create_order"))
        self.assertNotIn("coupon_id", self.client.session)


class OrderDetailViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Product", slug="product",
            price=20, stock=10
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        self.order = Order.objects.create(user=self.user, total_price=40)
        self.item = OrderItem.objects.create(
            order=self.order, product=self.product,
            quantity=2, price=20
        )

    def test_detail_redirects_anonymous(self):
        resp = self.client.get(reverse("orders:order_detail", args=[self.order.id]))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('orders:order_detail', args=[self.order.id])}"
        )

    def test_detail_status_code(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_detail", args=[self.order.id]))
        self.assertEqual(resp.status_code, 200)

    def test_detail_uses_correct_template(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_detail", args=[self.order.id]))
        self.assertTemplateUsed(resp, "orders/order_detail.html")

    def test_detail_context_contains_order(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_detail", args=[self.order.id]))
        self.assertEqual(resp.context["order"], self.order)

    def test_detail_other_user_gets_404(self):
        self.client.login(username="other@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_detail", args=[self.order.id]))
        self.assertEqual(resp.status_code, 404)

    def test_detail_nonexistent_order_returns_404(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_detail", args=[9999]))
        self.assertEqual(resp.status_code, 404)

    def test_detail_context_has_items(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_detail", args=[self.order.id]))
        self.assertTrue(resp.context["order"].items.exists())


class OrderListViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Product", slug="product",
            price=20, stock=10
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        self.order1 = Order.objects.create(user=self.user, total_price=40)
        self.order2 = Order.objects.create(user=self.user, total_price=100)
        self.other_order = Order.objects.create(user=self.other, total_price=50)

    def test_list_redirects_anonymous(self):
        resp = self.client.get(reverse("orders:order_list"))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('orders:order_list')}"
        )

    def test_list_status_code(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_list"))
        self.assertEqual(resp.status_code, 200)

    def test_list_uses_correct_template(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_list"))
        self.assertTemplateUsed(resp, "orders/order_list.html")

    def test_list_only_shows_own_orders(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_list"))
        orders = resp.context["orders"]
        self.assertIn(self.order1, orders)
        self.assertIn(self.order2, orders)
        self.assertNotIn(self.other_order, orders)

    def test_list_context_name(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_list"))
        self.assertEqual(resp.context["orders"].count(), 2)

    def test_list_empty_for_user_with_no_orders(self):
        empty_user = User.objects.create_user(
            username="empty", email="empty@example.com", password="pass123"
        )
        self.client.login(username="empty@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_list"))
        self.assertEqual(resp.context["orders"].count(), 0)

    def test_list_ordering_newest_first(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("orders:order_list"))
        orders = list(resp.context["orders"])
        self.assertEqual(orders[0], self.order2)
        self.assertEqual(orders[1], self.order1)
