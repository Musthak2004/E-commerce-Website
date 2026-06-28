from datetime import timedelta

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.utils import timezone

from coupons.models import Coupon
from products.models import Category, Product
from .models import Cart, CartItem, Wishlist
from .views import add_to_cart, remove_from_cart, update_quantity, cart_detail, toggle_wishlist
from .context_processors import cart_counts

User = get_user_model()


class CartModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cartuser",
            email="cart@example.com",
            password="pass123"
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_create_cart(self):
        self.assertEqual(self.cart.user, self.user)
        self.assertIsNotNone(self.cart.created_at)
        self.assertIsNotNone(self.cart.updated_at)

    def test_cart_str(self):
        self.assertEqual(str(self.cart), f"Cart - {self.user.email}")

    def test_cart_ordering(self):
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        other_cart = Cart.objects.create(user=other_user)
        qs = Cart.objects.all()
        self.assertEqual(qs.first(), other_cart)

    def test_cart_total_price_empty(self):
        self.assertEqual(self.cart.total_price, 0)

    def test_one_to_one_relationship(self):
        self.assertEqual(self.user.cart, self.cart)

    def test_cart_cascade_delete(self):
        cart_id = self.cart.id
        self.user.delete()
        self.assertFalse(Cart.objects.filter(id=cart_id).exists())


class CartItemModelTests(TestCase):
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
            username="cartuser", email="cart@example.com", password="pass123"
        )
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)

    def test_create_cart_item(self):
        self.assertEqual(self.item.quantity, 3)
        self.assertEqual(self.item.product, self.product)

    def test_cart_item_str(self):
        self.assertEqual(str(self.item), f"3x {self.product.name}")

    def test_cart_item_total_price(self):
        self.assertEqual(self.item.total_price, 75.00)

    def test_cart_item_ordering(self):
        p2 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Second", slug="second", price=10, stock=5
        )
        item2 = CartItem.objects.create(cart=self.cart, product=p2, quantity=1)
        qs = CartItem.objects.all()
        self.assertEqual(qs[0], self.item)
        self.assertEqual(qs[1], item2)

    def test_unique_cart_product_constraint(self):
        with self.assertRaises(Exception):
            CartItem.objects.create(cart=self.cart, product=self.product, quantity=5)

    def test_cart_item_cascade_on_cart_delete(self):
        item_id = self.item.id
        self.cart.delete()
        self.assertFalse(CartItem.objects.filter(id=item_id).exists())

    def test_cart_item_cascade_on_product_delete(self):
        item_id = self.item.id
        self.product.delete()
        self.assertFalse(CartItem.objects.filter(id=item_id).exists())

    def test_cart_total_price_with_items(self):
        self.assertEqual(self.cart.total_price, 75.00)
        p2 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Second", slug="second", price=10, stock=5
        )
        CartItem.objects.create(cart=self.cart, product=p2, quantity=2)
        self.assertEqual(self.cart.total_price, 95.00)

    def test_cart_item_quantity_minimum(self):
        self.item.quantity = 1
        self.item.save()
        self.assertEqual(self.item.quantity, 1)


class WishlistModelTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="wl_seller", email="wl_seller@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="WL Product", slug="wl-product",
            price=10, stock=5,
        )
        self.user = User.objects.create_user(
            username="wl_user", email="wl_user@example.com", password="pass123"
        )
        self.wishlist = Wishlist.objects.create(user=self.user)

    def test_create_wishlist(self):
        self.assertEqual(self.wishlist.user, self.user)
        self.assertIsNotNone(self.wishlist.created_at)

    def test_wishlist_str(self):
        self.assertEqual(str(self.wishlist), f"Wishlist - {self.user.email}")

    def test_wishlist_add_product(self):
        self.wishlist.products.add(self.product)
        self.assertIn(self.product, self.wishlist.products.all())

    def test_wishlist_cascade_delete(self):
        wl_id = self.wishlist.id
        self.user.delete()
        self.assertFalse(Wishlist.objects.filter(id=wl_id).exists())

    def test_wishlist_ordering(self):
        other = User.objects.create_user(
            username="wl_other", email="wl_other@example.com", password="pass123"
        )
        wl2 = Wishlist.objects.create(user=other)
        qs = Wishlist.objects.all()
        self.assertEqual(qs.first(), wl2)


class CartURLTests(TestCase):
    def test_cart_detail_url_resolves(self):
        resolver = resolve("/cart/")
        self.assertEqual(resolver.func, cart_detail)

    def test_cart_detail_url_name(self):
        url = reverse("cart:cart_detail")
        self.assertEqual(url, "/cart/")

    def test_add_to_cart_url_resolves(self):
        resolver = resolve("/cart/add/1/")
        self.assertEqual(resolver.func, add_to_cart)

    def test_add_to_cart_url_name(self):
        url = reverse("cart:add_to_cart", args=[1])
        self.assertEqual(url, "/cart/add/1/")

    def test_remove_from_cart_url_resolves(self):
        resolver = resolve("/cart/remove/1/")
        self.assertEqual(resolver.func, remove_from_cart)

    def test_remove_from_cart_url_name(self):
        url = reverse("cart:remove_from_cart", args=[1])
        self.assertEqual(url, "/cart/remove/1/")

    def test_update_quantity_url_resolves(self):
        resolver = resolve("/cart/update/1/")
        self.assertEqual(resolver.func, update_quantity)

    def test_update_quantity_url_name(self):
        url = reverse("cart:update_quantity", args=[1])
        self.assertEqual(url, "/cart/update/1/")


class WishlistURLTests(TestCase):
    def test_toggle_wishlist_url_resolves(self):
        resolver = resolve("/cart/wishlist/toggle/1/")
        self.assertEqual(resolver.func, toggle_wishlist)


class AddToCartViewTests(TestCase):
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
        self.unavailable = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Gone", slug="gone",
            price=10, stock=0, is_available=False
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )

    def test_add_to_cart_redirects_anonymous(self):
        resp = self.client.post(reverse("cart:add_to_cart", args=[self.product.id]))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('cart:add_to_cart', args=[self.product.id])}"
        )

    def test_add_to_cart_get_returns_405(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:add_to_cart", args=[self.product.id]))
        self.assertEqual(resp.status_code, 405)

    def test_add_to_cart_creates_cart_and_item(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:add_to_cart", args=[self.product.id]))
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.assertTrue(Cart.objects.filter(user=self.user).exists())
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(CartItem.objects.filter(cart=cart, product=self.product).exists())
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 1)

    def test_add_to_cart_increments_existing_item(self):
        self.client.login(username="cust@example.com", password="pass123")
        self.client.post(reverse("cart:add_to_cart", args=[self.product.id]))
        resp = self.client.post(reverse("cart:add_to_cart", args=[self.product.id]))
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_add_unavailable_product_returns_404(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:add_to_cart", args=[self.unavailable.id]))
        self.assertEqual(resp.status_code, 404)

    def test_add_nonexistent_product_returns_404(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:add_to_cart", args=[9999]))
        self.assertEqual(resp.status_code, 404)

    def test_add_to_cart_reuses_existing_cart(self):
        self.client.login(username="cust@example.com", password="pass123")
        Cart.objects.create(user=self.user)
        self.client.post(reverse("cart:add_to_cart", args=[self.product.id]))
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)


class RemoveFromCartViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Test", slug="test-prod",
            price=15, stock=5, is_available=True
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_remove_redirects_anonymous(self):
        resp = self.client.post(reverse("cart:remove_from_cart", args=[self.item.id]))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('cart:remove_from_cart', args=[self.item.id])}"
        )

    def test_remove_get_returns_405(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:remove_from_cart", args=[self.item.id]))
        self.assertEqual(resp.status_code, 405)

    def test_remove_own_item(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:remove_from_cart", args=[self.item.id]))
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.assertFalse(CartItem.objects.filter(id=self.item.id).exists())

    def test_remove_other_users_item_returns_404(self):
        self.client.login(username="other@example.com", password="pass123")
        resp = self.client.post(reverse("cart:remove_from_cart", args=[self.item.id]))
        self.assertEqual(resp.status_code, 404)

    def test_remove_nonexistent_item_returns_404(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:remove_from_cart", args=[9999]))
        self.assertEqual(resp.status_code, 404)


class UpdateQuantityViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Test", slug="test-prod",
            price=15, stock=5, is_available=True
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_update_redirects_anonymous(self):
        resp = self.client.post(reverse("cart:update_quantity", args=[self.item.id]))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('cart:update_quantity', args=[self.item.id])}"
        )

    def test_update_get_returns_405(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:update_quantity", args=[self.item.id]))
        self.assertEqual(resp.status_code, 405)

    def test_update_quantity(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:update_quantity", args=[self.item.id]), {"quantity": 5})
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 5)

    def test_update_quantity_to_zero_clamps_to_one(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:update_quantity", args=[self.item.id]), {"quantity": 0})
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)

    def test_update_quantity_to_negative_clamps_to_one(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:update_quantity", args=[self.item.id]), {"quantity": -5})
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)

    def test_update_quantity_invalid_value_clamps_to_one(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:update_quantity", args=[self.item.id]), {"quantity": "abc"})
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)

    def test_update_other_users_item_returns_404(self):
        self.client.login(username="other@example.com", password="pass123")
        resp = self.client.post(reverse("cart:update_quantity", args=[self.item.id]), {"quantity": 3})
        self.assertEqual(resp.status_code, 404)

    def test_update_nonexistent_item_returns_404(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:update_quantity", args=[9999]), {"quantity": 3})
        self.assertEqual(resp.status_code, 404)

    def test_update_missing_quantity_defaults_to_one(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.post(reverse("cart:update_quantity", args=[self.item.id]))
        self.assertRedirects(resp, reverse("cart:cart_detail"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)


class CartDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Product", slug="product",
            price=20, stock=10, is_available=True
        )
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)

    def test_detail_redirects_anonymous(self):
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('cart:cart_detail')}"
        )

    def test_detail_status_code(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(resp.status_code, 200)

    def test_detail_uses_correct_template(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertTemplateUsed(resp, "cart/cart_detail.html")

    def test_detail_context_contains_cart(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertIn("cart", resp.context)
        self.assertEqual(resp.context["cart"], self.cart)

    def test_detail_context_cart_has_items(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertTrue(resp.context["cart"].items.exists())

    def test_detail_empty_cart(self):
        self.item.delete()
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context["cart"])
        self.assertFalse(resp.context["cart"].items.exists())

    def test_detail_context_has_coupon_keys(self):
        self.client.login(username="cust@example.com", password="pass123")
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertIn("coupon", resp.context)
        self.assertIn("discount_amount", resp.context)
        self.assertIn("total_after_discount", resp.context)

    def test_detail_with_valid_coupon(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="CART10", discount_type="PERCENTAGE", discount_value=10,
            valid_from=now - timedelta(days=1), valid_to=now + timedelta(days=30),
        )
        self.client.login(username="cust@example.com", password="pass123")
        session = self.client.session
        session["coupon_id"] = coupon.id
        session.save()
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(resp.context["coupon"], coupon)
        self.assertEqual(resp.context["discount_amount"], 6.00)

    def test_detail_with_expired_coupon_in_session(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="EXPIRED", discount_type="PERCENTAGE", discount_value=10,
            valid_from=now - timedelta(days=60), valid_to=now - timedelta(days=1),
        )
        self.client.login(username="cust@example.com", password="pass123")
        session = self.client.session
        session["coupon_id"] = coupon.id
        session.save()
        resp = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(resp.context["coupon"], coupon)
        self.assertEqual(resp.context["discount_amount"], 0)
        self.assertEqual(resp.context["total_after_discount"], 60.00)


class CartContextProcessorTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Product", slug="product",
            price=20, stock=10, is_available=True
        )
        self.user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )

    def test_anonymous_user_returns_none(self):
        request = type("Request", (), {"user": type("User", (), {"is_authenticated": False})()})()
        result = cart_counts(request)
        self.assertIsNone(result["cart_count"])
        self.assertIsNone(result["wishlist_count"])

    def test_authenticated_user_no_cart(self):
        request = type("Request", (), {"user": self.user})()
        result = cart_counts(request)
        self.assertEqual(result["cart_count"], 0)
        self.assertEqual(result["wishlist_count"], 0)

    def test_authenticated_user_with_cart_items(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        request = type("Request", (), {"user": self.user})()
        result = cart_counts(request)
        self.assertEqual(result["cart_count"], 1)
        self.assertEqual(result["wishlist_count"], 0)

    def test_authenticated_user_with_empty_cart(self):
        Cart.objects.create(user=self.user)
        request = type("Request", (), {"user": self.user})()
        result = cart_counts(request)
        self.assertEqual(result["cart_count"], 0)
        self.assertEqual(result["wishlist_count"], 0)

    def test_wishlist_count_in_context_processor(self):
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist.products.add(self.product)
        request = type("Request", (), {"user": self.user})()
        result = cart_counts(request)
        self.assertEqual(result["wishlist_count"], 1)


class WishlistViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller_w", email="seller_w@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Wishlist Product", slug="wishlist-product",
            price=25.00, stock=10, is_available=True
        )
        self.unavailable = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Gone", slug="gone",
            price=10, stock=0, is_available=False
        )
        self.user = User.objects.create_user(
            username="cust_w", email="cust_w@example.com", password="pass123"
        )

    def test_toggle_adds_to_wishlist(self):
        self.client.login(username="cust_w@example.com", password="pass123")
        resp = self.client.post(reverse("cart:toggle_wishlist", args=[self.product.id]))
        self.assertRedirects(resp, reverse("products:product_list"))
        wishlist = Wishlist.objects.get(user=self.user)
        self.assertIn(self.product, wishlist.products.all())

    def test_toggle_removes_from_wishlist(self):
        self.client.login(username="cust_w@example.com", password="pass123")
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist.products.add(self.product)
        self.client.post(reverse("cart:toggle_wishlist", args=[self.product.id]))
        wishlist.refresh_from_db()
        self.assertNotIn(self.product, wishlist.products.all())

    def test_toggle_redirects_anonymous(self):
        resp = self.client.post(reverse("cart:toggle_wishlist", args=[self.product.id]))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('cart:toggle_wishlist', args=[self.product.id])}"
        )

    def test_toggle_unavailable_product_returns_404(self):
        self.client.login(username="cust_w@example.com", password="pass123")
        resp = self.client.post(reverse("cart:toggle_wishlist", args=[self.unavailable.id]))
        self.assertEqual(resp.status_code, 404)
