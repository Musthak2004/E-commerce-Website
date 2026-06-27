from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model

from .models import Profile
from .forms import SignUpForm
from .views import ProfileUpdateView, SignUpView

User = get_user_model()


class CustomUserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.user_type, "CUSTOMER")
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.user_type, "CUSTOMER")

    def test_email_unique(self):
        User.objects.create_user(
            username="user1",
            email="same@example.com",
            password="pass123"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="user2",
                email="same@example.com",
                password="pass456"
            )

    def test_user_str(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )
        self.assertEqual(str(user), "test@example.com")

    def test_user_type_choices(self):
        user = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="pass123",
            user_type="SELLER"
        )
        self.assertEqual(user.user_type, "SELLER")

    def test_default_user_type(self):
        user = User.objects.create_user(
            username="default",
            email="default@example.com",
            password="pass123"
        )
        self.assertEqual(user.user_type, "CUSTOMER")

    def test_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields(self):
        self.assertIn("username", User.REQUIRED_FIELDS)


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )

    def test_profile_created_on_user_creation(self):
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_str(self):
        self.assertEqual(str(self.user.profile), "test@example.com")

    def test_profile_default_fields_empty(self):
        profile = self.user.profile
        self.assertEqual(profile.full_name, "")
        self.assertEqual(profile.address, "")
        self.assertEqual(profile.city, "")
        self.assertEqual(profile.country, "")
        self.assertEqual(profile.postal_code, "")

    def test_profile_update(self):
        profile = self.user.profile
        profile.full_name = "John Doe"
        profile.city = "New York"
        profile.country = "USA"
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, "John Doe")
        self.assertEqual(profile.city, "New York")

    def test_profile_cascade_delete(self):
        profile_id = self.user.profile.id
        self.user.delete()
        with self.assertRaises(Profile.DoesNotExist):
            Profile.objects.get(id=profile_id)


class SignUpFormTests(TestCase):
    def test_form_has_correct_fields(self):
        form = SignUpForm()
        expected_fields = ["username", "email", "user_type", "phone_number", "password1", "password2"]
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_valid_signup_form(self):
        form_data = {
            "username": "newuser",
            "email": "new@example.com",
            "user_type": "CUSTOMER",
            "phone_number": "+1234567890",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_blank_data(self):
        form = SignUpForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("password1", form.errors)
        self.assertIn("password2", form.errors)

    def test_password_mismatch(self):
        form_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "StrongPass123!",
            "password2": "DifferentPass456!",
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="pass123"
        )
        form_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "user_type": "CUSTOMER",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_email(self):
        form_data = {
            "username": "newuser",
            "email": "not-an-email",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())


class SignUpViewTests(TestCase):
    def test_signup_url_resolves(self):
        resolver = resolve("/accounts/signup/")
        self.assertEqual(resolver.func.view_class, SignUpView)

    def test_signup_url_name(self):
        url = reverse("signup")
        self.assertEqual(url, "/accounts/signup/")

    def test_signup_get(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")
        self.assertIsInstance(response.context["form"], SignUpForm)

    def test_signup_post_creates_user_and_profile(self):
        response = self.client.post(reverse("signup"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "user_type": "CUSTOMER",
            "phone_number": "+1234567890",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())
        user = User.objects.get(email="newuser@example.com")
        self.assertTrue(hasattr(user, "profile"))

    def test_signup_post_invalid_data(self):
        response = self.client.post(reverse("signup"), {
            "username": "",
            "email": "bad",
            "password1": "pw1",
            "password2": "pw2",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")
        self.assertFalse(response.context["form"].is_valid())

    def test_signup_post_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="dup@example.com",
            password="pass123"
        )
        response = self.client.post(reverse("signup"), {
            "username": "newuser",
            "email": "dup@example.com",
            "user_type": "CUSTOMER",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)


class SignalTests(TestCase):
    def test_profile_created_on_user_creation(self):
        user = User.objects.create_user(
            username="signaltest",
            email="signal@example.com",
            password="pass123"
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_not_duplicated_on_save(self):
        user = User.objects.create_user(
            username="signaltest2",
            email="signal2@example.com",
            password="pass123"
        )
        Profile.objects.count()
        user.save()
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)


class AuthURLTests(TestCase):
    def test_login_url_resolves(self):
        url = reverse("login")
        self.assertEqual(url, "/accounts/login/")

    def test_logout_url_resolves(self):
        url = reverse("logout")
        self.assertEqual(url, "/accounts/logout/")

    def test_home_url_resolves(self):
        url = reverse("home")
        self.assertEqual(url, "/")

    def test_login_page_uses_correct_template(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_logged_in_user_can_access_home(self):
        User.objects.create_user(
            username="loggedin",
            email="logged@example.com",
            password="pass123"
        )
        self.client.login(username="logged@example.com", password="pass123")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects(self):
        User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="pass123"
        )
        self.client.login(username="logout@example.com", password="pass123")
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)


class ProfileUpdateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="pass123"
        )

    def test_profile_get_redirects_anonymous(self):
        resp = self.client.get(reverse("profile"))
        self.assertRedirects(
            resp, f"{reverse('login')}?next={reverse('profile')}"
        )

    def test_profile_get_status_code(self):
        self.client.login(username="profile@example.com", password="pass123")
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, 200)

    def test_profile_get_uses_correct_template(self):
        self.client.login(username="profile@example.com", password="pass123")
        resp = self.client.get(reverse("profile"))
        self.assertTemplateUsed(resp, "accounts/profile_form.html")

    def test_profile_update(self):
        self.client.login(username="profile@example.com", password="pass123")
        resp = self.client.post(reverse("profile"), {
            "full_name": "John Doe",
            "address": "123 Main St",
            "city": "New York",
            "country": "USA",
            "postal_code": "10001",
        })
        self.assertRedirects(resp, reverse("home"))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, "John Doe")
        self.assertEqual(self.user.profile.city, "New York")

    def test_profile_auto_created(self):
        self.client.login(username="profile@example.com", password="pass123")
        Profile.objects.filter(user=self.user).delete()
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
