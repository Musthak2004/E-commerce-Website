from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve

from .forms import ContactForm
from .models import ContactMessage, NewsletterSubscriber
from .views import HomePageView, AboutPageView, ContactPageView

User = get_user_model()


class PageURLTests(TestCase):
    def test_home_url_resolves(self):
        resolver = resolve("/")
        self.assertEqual(resolver.func.view_class, HomePageView)

    def test_home_url_name(self):
        url = reverse("home")
        self.assertEqual(url, "/")

    def test_contact_url_resolves(self):
        resolver = resolve("/contact/")
        self.assertEqual(resolver.func.view_class, ContactPageView)

    def test_about_url_resolves(self):
        resolver = resolve("/about/")
        self.assertEqual(resolver.func.view_class, AboutPageView)


class HomeViewTests(TestCase):
    def test_homepage_status_code(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_homepage_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home.html")


class AboutViewTests(TestCase):
    def test_about_status_code(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_about_uses_correct_template(self):
        response = self.client.get(reverse("about"))
        self.assertTemplateUsed(response, "about.html")


class ContactMessageModelTests(TestCase):
    def test_create_contact_message(self):
        msg = ContactMessage.objects.create(
            name="John Doe",
            email="john@example.com",
            subject="general",
            message="Hello, I have a question.",
        )
        self.assertEqual(msg.name, "John Doe")
        self.assertEqual(msg.subject, "general")

    def test_contact_message_str(self):
        msg = ContactMessage.objects.create(
            name="Jane", email="jane@example.com",
            subject="order", message="Where is my order?",
        )
        self.assertEqual(str(msg), "Jane — order")

    def test_contact_message_ordering(self):
        ContactMessage.objects.create(
            name="A", email="a@a.com", subject="general", message="First",
        )
        ContactMessage.objects.create(
            name="B", email="b@b.com", subject="general", message="Second",
        )
        qs = ContactMessage.objects.all()
        self.assertEqual(qs[0].name, "B")


class NewsletterSubscriberModelTests(TestCase):
    def test_create_subscriber(self):
        sub = NewsletterSubscriber.objects.create(email="sub@example.com")
        self.assertEqual(sub.email, "sub@example.com")
        self.assertTrue(sub.is_active)
        self.assertIsNotNone(sub.subscribed_at)

    def test_subscriber_str(self):
        sub = NewsletterSubscriber.objects.create(email="sub@example.com")
        self.assertEqual(str(sub), "sub@example.com")

    def test_subscriber_unique_email(self):
        NewsletterSubscriber.objects.create(email="dup@example.com")
        with self.assertRaises(Exception):
            NewsletterSubscriber.objects.create(email="dup@example.com")

    def test_subscriber_ordering(self):
        NewsletterSubscriber.objects.create(email="first@example.com")
        NewsletterSubscriber.objects.create(email="second@example.com")
        qs = NewsletterSubscriber.objects.all()
        self.assertEqual(qs[0].email, "second@example.com")


class ContactFormTests(TestCase):
    def test_form_has_correct_fields(self):
        form = ContactForm()
        expected = ["name", "email", "subject", "message"]
        for field in expected:
            self.assertIn(field, form.fields)

    def test_valid_form(self):
        form = ContactForm(data={
            "name": "John", "email": "john@example.com",
            "subject": "general", "message": "Hello!",
        })
        self.assertTrue(form.is_valid())

    def test_blank_form_invalid(self):
        form = ContactForm(data={})
        self.assertFalse(form.is_valid())

    def test_invalid_email(self):
        form = ContactForm(data={
            "name": "John", "email": "not-an-email",
            "subject": "general", "message": "Hello!",
        })
        self.assertFalse(form.is_valid())


class ContactPageViewTests(TestCase):
    def test_get_status_code(self):
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)

    def test_get_uses_correct_template(self):
        response = self.client.get(reverse("contact"))
        self.assertTemplateUsed(response, "contact.html")

    def test_get_has_form(self):
        response = self.client.get(reverse("contact"))
        self.assertIsInstance(response.context["form"], ContactForm)

    def test_post_valid_creates_message(self):
        response = self.client.post(reverse("contact"), {
            "name": "John", "email": "john@example.com",
            "subject": "general", "message": "Hello, help!",
        })
        self.assertRedirects(response, "/contact/")
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_post_invalid_rerenders(self):
        response = self.client.post(reverse("contact"), {
            "name": "", "email": "bad",
            "subject": "", "message": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contact.html")


class NewsletterSignupTests(TestCase):
    def test_valid_email_creates_subscriber(self):
        response = self.client.post("/newsletter/", {"email": "sub@example.com"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(NewsletterSubscriber.objects.filter(email="sub@example.com").exists())

    def test_duplicate_email_does_not_error(self):
        NewsletterSubscriber.objects.create(email="dup@example.com")
        response = self.client.post("/newsletter/", {"email": "dup@example.com"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_invalid_email_shows_error(self):
        response = self.client.post("/newsletter/", {"email": "not-an-email"})
        self.assertEqual(response.status_code, 302)

    def test_empty_email_shows_error(self):
        response = self.client.post("/newsletter/", {"email": ""})
        self.assertEqual(response.status_code, 302)

    def test_get_request_returns_405(self):
        response = self.client.get("/newsletter/")
        self.assertEqual(response.status_code, 405)


class AdminDashboardTests(TestCase):
    def test_non_staff_redirected_to_admin_login(self):
        user = User.objects.create_user(
            username="cust", email="cust@example.com", password="pass123"
        )
        self.client.login(username="cust@example.com", password="pass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertRedirects(response, f"/admin/login/?next={reverse('admin_dashboard')}")

    def test_staff_can_access(self):
        staff = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass123"
        )
        self.client.login(username="admin@example.com", password="pass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/dashboard.html")
        self.assertIn("total_users", response.context)
        self.assertIn("total_products", response.context)
        self.assertIn("total_orders", response.context)
        self.assertIn("total_revenue", response.context)
