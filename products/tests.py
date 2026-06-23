from decimal import Decimal

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model

from .models import Category, Product, ProductImage
from .forms import ProductForm
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

User = get_user_model()


class CategoryModelTests(TestCase):
    def test_create_category(self):
        cat = Category.objects.create(name="Home & Living", slug="home-living")
        self.assertEqual(cat.name, "Home & Living")
        self.assertEqual(cat.slug, "home-living")

    def test_category_str(self):
        cat = Category.objects.create(name="Kitchen", slug="kitchen")
        self.assertEqual(str(cat), "Kitchen")

    def test_category_verbose_name_plural(self):
        self.assertEqual(Category._meta.verbose_name_plural, "Categories")

    def test_category_ordering(self):
        Category.objects.create(name="Bath", slug="bath")
        Category.objects.create(name="Home", slug="home")
        qs = Category.objects.all()
        self.assertEqual(qs[0].name, "Bath")
        self.assertEqual(qs[1].name, "Home")


class ProductModelTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller1", email="seller@example.com",
            password="pass123", user_type="SELLER"
        )
        self.cat = Category.objects.create(name="Home", slug="home")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Test Product", slug="test-product",
            description="A test product.", price=29.99, stock=10,
        )

    def test_create_product(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, 29.99)
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.is_available)

    def test_product_str(self):
        self.assertEqual(str(self.product), "Test Product")

    def test_product_defaults(self):
        self.assertTrue(self.product.is_available)
        self.assertEqual(self.product.stock, 10)

    def test_product_ordering(self):
        Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Older", slug="older", price=10, stock=1,
        )
        qs = Product.objects.all()
        self.assertEqual(qs[0].name, "Older")

    def test_product_seller_relationship(self):
        self.assertEqual(self.product.seller, self.seller)
        self.assertIn(self.product, self.seller.products.all())

    def test_product_category_relationship(self):
        self.assertEqual(self.product.category, self.cat)
        self.assertIn(self.product, self.cat.products.all())

    def test_product_on_delete_seller_cascade(self):
        self.seller.delete()
        self.assertEqual(Product.objects.count(), 0)

    def test_product_on_delete_category_set_null(self):
        self.cat.delete()
        self.product.refresh_from_db()
        self.assertIsNone(self.product.category)


class ProductImageModelTests(TestCase):
    def setUp(self):
        seller = User.objects.create_user(
            username="seller2", email="seller2@example.com",
            password="pass123", user_type="SELLER"
        )
        cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            seller=seller, category=cat,
            name="Test", slug="test-prod", price=10, stock=5,
        )

    def test_product_image_str(self):
        img = ProductImage.objects.create(product=self.product)
        self.assertEqual(str(img), f"Image of {self.product.name}")

    def test_product_image_relationship(self):
        img = ProductImage.objects.create(product=self.product)
        self.assertIn(img, self.product.images.all())


class ProductFormTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Test", slug="test")

    def test_form_has_correct_fields(self):
        form = ProductForm()
        expected = ["category", "name", "slug", "description", "price", "stock", "image", "is_available"]
        for field in expected:
            self.assertIn(field, form.fields)

    def test_valid_form(self):
        form = ProductForm(data={
            "category": self.cat.id,
            "name": "New Product",
            "slug": "new-product",
            "description": "A new product.",
            "price": 49.99,
            "stock": 20,
            "is_available": True,
        })
        self.assertTrue(form.is_valid())

    def test_blank_data(self):
        form = ProductForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("price", form.errors)

    def test_price_zero_invalid(self):
        form = ProductForm(data={
            "category": self.cat.id,
            "name": "Free Item", "slug": "free-item",
            "price": 0, "stock": 5,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_price_negative_invalid(self):
        form = ProductForm(data={
            "category": self.cat.id,
            "name": "Bad", "slug": "bad",
            "price": -10, "stock": 5,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_stock_negative_invalid(self):
        form = ProductForm(data={
            "category": self.cat.id,
            "name": "Bad", "slug": "bad",
            "price": 10, "stock": -1,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("stock", form.errors)


class ProductURLTests(TestCase):
    def test_product_list_url_resolves(self):
        resolver = resolve("/products/")
        self.assertEqual(resolver.func.view_class, ProductListView)

    def test_product_list_url_name(self):
        url = reverse("products:product_list")
        self.assertEqual(url, "/products/")

    def test_product_create_url_resolves(self):
        resolver = resolve("/products/create/")
        self.assertEqual(resolver.func.view_class, ProductCreateView)

    def test_product_create_url_name(self):
        url = reverse("products:product_create")
        self.assertEqual(url, "/products/create/")

    def test_product_detail_url_resolves(self):
        resolver = resolve("/products/test-slug/")
        self.assertEqual(resolver.func.view_class, ProductDetailView)

    def test_product_update_url_resolves(self):
        resolver = resolve("/products/test-slug/update/")
        self.assertEqual(resolver.func.view_class, ProductUpdateView)

    def test_product_delete_url_resolves(self):
        resolver = resolve("/products/test-slug/delete/")
        self.assertEqual(resolver.func.view_class, ProductDeleteView)


class ProductListViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller3", email="seller3@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat = Category.objects.create(name="Cat", slug="cat")
        self.p1 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Available", slug="available",
            price=10, stock=5, is_available=True,
        )
        self.p2 = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Unavailable", slug="unavailable",
            price=10, stock=0, is_available=False,
        )

    def test_list_status_code(self):
        resp = self.client.get(reverse("products:product_list"))
        self.assertEqual(resp.status_code, 200)

    def test_list_uses_correct_template(self):
        resp = self.client.get(reverse("products:product_list"))
        self.assertTemplateUsed(resp, "products/product_list.html")

    def test_list_only_shows_available_products(self):
        resp = self.client.get(reverse("products:product_list"))
        products = resp.context["products"]
        self.assertIn(self.p1, products)
        self.assertNotIn(self.p2, products)

    def test_list_context_name(self):
        resp = self.client.get(reverse("products:product_list"))
        self.assertEqual(resp.context["object_list"].count(), 1)


class ProductDetailViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller4", email="seller4@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Detail Product", slug="detail-product",
            price=25, stock=8, is_available=True,
        )
        self.unavailable = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Gone", slug="gone",
            price=10, stock=0, is_available=False,
        )

    def test_detail_status_code(self):
        resp = self.client.get(reverse("products:product_detail", args=[self.product.slug]))
        self.assertEqual(resp.status_code, 200)

    def test_detail_uses_correct_template(self):
        resp = self.client.get(reverse("products:product_detail", args=[self.product.slug]))
        self.assertTemplateUsed(resp, "products/product_detail.html")

    def test_detail_context(self):
        resp = self.client.get(reverse("products:product_detail", args=[self.product.slug]))
        self.assertEqual(resp.context["product"], self.product)

    def test_unavailable_product_returns_404(self):
        resp = self.client.get(reverse("products:product_detail", args=[self.unavailable.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_product_returns_404(self):
        resp = self.client.get("/products/no-exist/")
        self.assertEqual(resp.status_code, 404)


class ProductCreateViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller5", email="seller5@example.com",
            password="pass123", user_type="SELLER",
        )
        self.customer = User.objects.create_user(
            username="cust1", email="cust1@example.com",
            password="pass123", user_type="CUSTOMER",
        )
        self.cat = Category.objects.create(name="Cat", slug="cat")

    def test_create_get_redirects_anonymous(self):
        resp = self.client.get(reverse("products:product_create"))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('products:product_create')}")

    def test_create_get_forbidden_for_customer(self):
        self.client.login(username="cust1@example.com", password="pass123")
        resp = self.client.get(reverse("products:product_create"))
        self.assertEqual(resp.status_code, 403)

    def test_create_get_shows_form_for_seller(self):
        self.client.login(username="seller5@example.com", password="pass123")
        resp = self.client.get(reverse("products:product_create"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "products/product_form.html")
        self.assertIsInstance(resp.context["form"], ProductForm)

    def test_create_post_creates_product(self):
        self.client.login(username="seller5@example.com", password="pass123")
        resp = self.client.post(reverse("products:product_create"), {
            "category": self.cat.id,
            "name": "New Item",
            "slug": "new-item",
            "description": "Brand new.",
            "price": 39.99,
            "stock": 15,
            "is_available": True,
        })
        self.assertRedirects(resp, reverse("products:product_list"))
        self.assertTrue(Product.objects.filter(slug="new-item").exists())
        p = Product.objects.get(slug="new-item")
        self.assertEqual(p.seller, self.seller)

    def test_create_post_forbidden_for_customer(self):
        self.client.login(username="cust1@example.com", password="pass123")
        resp = self.client.post(reverse("products:product_create"), {
            "name": "Hack", "slug": "hack", "price": 1, "stock": 1,
        })
        self.assertEqual(resp.status_code, 403)

    def test_create_post_invalid_rerenders_form(self):
        self.client.login(username="seller5@example.com", password="pass123")
        resp = self.client.post(reverse("products:product_create"), {
            "name": "", "price": 0, "stock": -1,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "products/product_form.html")
        self.assertFalse(resp.context["form"].is_valid())


class ProductUpdateViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller6", email="seller6@example.com",
            password="pass123", user_type="SELLER",
        )
        self.other_seller = User.objects.create_user(
            username="seller7", email="seller7@example.com",
            password="pass123", user_type="SELLER",
        )
        self.customer = User.objects.create_user(
            username="cust2", email="cust2@example.com",
            password="pass123", user_type="CUSTOMER",
        )
        self.cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Editable", slug="editable",
            price=20, stock=5,
        )

    def test_update_get_redirects_anonymous(self):
        resp = self.client.get(reverse("products:product_update", args=[self.product.slug]))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('products:product_update', args=[self.product.slug])}"
        )

    def test_update_get_forbidden_for_customer(self):
        self.client.login(username="cust2@example.com", password="pass123")
        resp = self.client.get(reverse("products:product_update", args=[self.product.slug]))
        self.assertEqual(resp.status_code, 403)

    def test_update_get_forbidden_for_other_seller(self):
        self.client.login(username="seller7@example.com", password="pass123")
        resp = self.client.get(reverse("products:product_update", args=[self.product.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_update_get_shows_form_for_owner(self):
        self.client.login(username="seller6@example.com", password="pass123")
        resp = self.client.get(reverse("products:product_update", args=[self.product.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "products/product_form.html")

    def test_update_post_updates_product(self):
        self.client.login(username="seller6@example.com", password="pass123")
        resp = self.client.post(
            reverse("products:product_update", args=[self.product.slug]),
            {
                "category": self.cat.id,
                "name": "Updated Name",
                "slug": "editable",
                "price": 99.99,
                "stock": 50,
                "is_available": True,
            },
        )
        self.assertRedirects(resp, reverse("products:product_list"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Updated Name")
        self.assertEqual(self.product.price, Decimal("99.99"))
        self.assertEqual(self.product.stock, 50)


class ProductDeleteViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller8", email="seller8@example.com",
            password="pass123", user_type="SELLER",
        )
        self.other_seller = User.objects.create_user(
            username="seller9", email="seller9@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Deletable", slug="deletable",
            price=15, stock=3,
        )

    def test_delete_get_forbidden_for_other_seller(self):
        self.client.login(username="seller9@example.com", password="pass123")
        resp = self.client.get(reverse("products:product_delete", args=[self.product.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_delete_get_shows_confirm_for_owner(self):
        self.client.login(username="seller8@example.com", password="pass123")
        resp = self.client.get(reverse("products:product_delete", args=[self.product.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "products/product_confirm_delete.html")

    def test_delete_post_deletes_product(self):
        self.client.login(username="seller8@example.com", password="pass123")
        resp = self.client.post(reverse("products:product_delete", args=[self.product.slug]))
        self.assertRedirects(resp, reverse("products:product_list"))
        self.assertFalse(Product.objects.filter(slug="deletable").exists())
