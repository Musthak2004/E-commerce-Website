from decimal import Decimal

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model

from reviews.models import Review
from .models import Category, Product, ProductImage, Tag
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


class TagModelTests(TestCase):
    def test_create_tag(self):
        tag = Tag.objects.create(name="Sale", slug="sale")
        self.assertEqual(tag.name, "Sale")
        self.assertEqual(tag.slug, "sale")

    def test_tag_str(self):
        tag = Tag.objects.create(name="New", slug="new")
        self.assertEqual(str(tag), "New")

    def test_tag_ordering(self):
        Tag.objects.create(name="B", slug="b")
        Tag.objects.create(name="A", slug="a")
        qs = Tag.objects.all()
        self.assertEqual(qs[0].name, "A")
        self.assertEqual(qs[1].name, "B")

    def test_tag_unique(self):
        Tag.objects.create(name="Unique", slug="unique")
        with self.assertRaises(Exception):
            Tag.objects.create(name="Unique", slug="unique")


class ProductModelPropertyTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller_prop", email="seller_prop@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Rated Product", slug="rated-product",
            price=20, stock=5,
        )

    def test_average_rating_no_reviews(self):
        self.assertIsNone(self.product.average_rating)

    def test_average_rating_with_reviews(self):
        user = User.objects.create_user(
            username="reviewer", email="reviewer@example.com", password="pass123"
        )
        Review.objects.create(user=user, product=self.product, rating=4)
        Review.objects.create(
            user=User.objects.create_user(
                username="reviewer2", email="reviewer2@example.com", password="pass123"
            ),
            product=self.product, rating=5,
        )
        self.assertEqual(self.product.average_rating, 4.5)

    def test_review_count_zero(self):
        self.assertEqual(self.product.review_count, 0)

    def test_review_count_with_reviews(self):
        user = User.objects.create_user(
            username="reviewer3", email="reviewer3@example.com", password="pass123"
        )
        Review.objects.create(user=user, product=self.product, rating=3)
        self.assertEqual(self.product.review_count, 1)


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
        expected = ["category", "tags", "name", "slug", "description", "price", "stock", "image", "is_available"]
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

    def test_search_by_name(self):
        p = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Test Product", slug="test-product",
            price=15, stock=3, is_available=True,
        )
        resp = self.client.get(reverse("products:product_list"), {"q": "Test"})
        self.assertIn(p, resp.context["products"])

    def test_search_by_description(self):
        p = Product.objects.create(
            seller=self.seller, category=self.cat,
            name="Searchable", slug="searchable",
            price=10, stock=5, is_available=True,
            description="This product has a keyword in the description.",
        )
        resp = self.client.get(reverse("products:product_list"), {"q": "keyword"})
        self.assertIn(p, resp.context["products"])

    def test_search_no_results(self):
        resp = self.client.get(reverse("products:product_list"), {"q": "xyzzy"})
        self.assertEqual(resp.context["products"].count(), 0)

    def test_search_empty_query(self):
        resp = self.client.get(reverse("products:product_list"), {"q": ""})
        self.assertEqual(resp.context["products"].count(), 1)
        self.assertIn(self.p1, resp.context["products"])

    def test_search_context_has_query(self):
        resp = self.client.get(reverse("products:product_list"), {"q": "Available"})
        self.assertEqual(resp.context["query"], "Available")


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


class ProductListViewFilterSortTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller_fs", email="seller_fs@example.com",
            password="pass123", user_type="SELLER",
        )
        self.cat1 = Category.objects.create(name="Electronics", slug="electronics")
        self.cat2 = Category.objects.create(name="Books", slug="books")
        self.tag1 = Tag.objects.create(name="Sale", slug="sale")
        self.tag2 = Tag.objects.create(name="New", slug="new")
        self.p1 = Product.objects.create(
            seller=self.seller, category=self.cat1,
            name="A Product", slug="a-product",
            price=50, stock=5, is_available=True,
        )
        self.p2 = Product.objects.create(
            seller=self.seller, category=self.cat2,
            name="Z Product", slug="z-product",
            price=10, stock=5, is_available=True,
        )
        self.p3 = Product.objects.create(
            seller=self.seller, category=self.cat1,
            name="Middle", slug="middle",
            price=30, stock=5, is_available=True,
        )
        self.p1.tags.add(self.tag1)
        self.p2.tags.add(self.tag2)
        self.p3.tags.add(self.tag1, self.tag2)

    def test_filter_by_category(self):
        resp = self.client.get(reverse("products:product_list"), {"category": "electronics"})
        products = resp.context["products"]
        self.assertIn(self.p1, products)
        self.assertIn(self.p3, products)
        self.assertNotIn(self.p2, products)

    def test_filter_by_tag(self):
        resp = self.client.get(reverse("products:product_list"), {"tag": "sale"})
        products = resp.context["products"]
        self.assertIn(self.p1, products)
        self.assertIn(self.p3, products)
        self.assertNotIn(self.p2, products)

    def test_sort_price_asc(self):
        resp = self.client.get(reverse("products:product_list"), {"sort": "price_asc"})
        products = list(resp.context["products"])
        self.assertEqual(products[0].price, 10)
        self.assertEqual(products[1].price, 30)
        self.assertEqual(products[2].price, 50)

    def test_sort_price_desc(self):
        resp = self.client.get(reverse("products:product_list"), {"sort": "price_desc"})
        products = list(resp.context["products"])
        self.assertEqual(products[0].price, 50)
        self.assertEqual(products[1].price, 30)
        self.assertEqual(products[2].price, 10)

    def test_sort_name(self):
        resp = self.client.get(reverse("products:product_list"), {"sort": "name"})
        products = list(resp.context["products"])
        self.assertEqual(products[0].name, "A Product")
        self.assertEqual(products[1].name, "Middle")
        self.assertEqual(products[2].name, "Z Product")

    def test_sort_oldest(self):
        resp = self.client.get(reverse("products:product_list"), {"sort": "oldest"})
        products = list(resp.context["products"])
        self.assertEqual(products[0], self.p1)

    def test_context_has_categories(self):
        resp = self.client.get(reverse("products:product_list"))
        self.assertIn("categories", resp.context)
        self.assertIn("tags", resp.context)
        self.assertIn("current_category", resp.context)
        self.assertIn("current_sort", resp.context)
        self.assertIn("current_tag", resp.context)
        self.assertIn("query", resp.context)


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
