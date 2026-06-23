# E-commerce Website

A Django-based e-commerce platform with a clean, minimal UI. Features user authentication, product management, and a refined shopping experience.

## Features

- **User Authentication** — Login, signup, password reset (email-based auth with `CustomUser` model)
- **Role-Based Access** — Customer and Seller roles with profile management; redirects for authenticated users
- **Product Management** — Sellers can create, edit, and delete products; product listing with pagination and images
- **Responsive Design** — Works on desktop, tablet, and mobile
- **Clean UI** — Warm minimal aesthetic with gold accents, Playfair Display + Outfit fonts

## Tech Stack

- **Backend:** Django 6.0, Python 3.13
- **Frontend:** HTML5, CSS3, vanilla JavaScript
- **Database:** SQLite (default)
- **Auth:** `django.contrib.auth` with custom `AbstractUser` model (`USERNAME_FIELD = "email"`)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Musthak2004/E-commerce-Website.git
cd E-commerce-Website

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install django pillow

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the app.

## Test Account

| Email | Password | Role |
|-------|----------|------|
| testuser@gmail.com | test_2004 | Seller |

## Running Tests

```bash
# Run all tests
python manage.py test --verbosity=2

# Run specific app tests
python manage.py test accounts --verbosity=2
python manage.py test pages --verbosity=2
```

## Project Structure

```
├── accounts/            # User auth app (models, forms, views, admin)
│   ├── models.py        # CustomUser (email-based), Profile
│   ├── forms.py         # SignUpForm with duplicate email validation
│   ├── views.py         # SignUpView (redirects authenticated users)
│   ├── tests.py         # 33 tests (models, forms, views, signals, URLs)
│   └── signals.py       # Auto-create Profile on user signup
├── pages/               # Page routing app
│   ├── views.py         # HomePageView
│   ├── urls.py          # Root URL routing
│   └── tests.py         # 4 tests (URLs, templates)
├── products/            # Product management app
│   ├── models.py        # Category, Product, ProductImage
│   ├── forms.py         # ProductForm (price/stock validation)
│   ├── views.py         # CRUD views with seller-only access
│   ├── urls.py          # Product routes (list, detail, create, update, delete)
│   ├── admin.py         # Admin config with inline images
│   ├── tests.py         # Test suite
│   └── templates/products/
│       ├── product_list.html
│       ├── product_detail.html
│       ├── product_form.html
│       └── product_confirm_delete.html
├── django_project/      # Project settings and URLs (media serving in dev)
├── media/products/      # Uploaded product images
├── static/
│   ├── css/style.css    # Complete stylesheet
│   └── js/main.js       # Frontend interactions (nav, search, password toggle, alerts)
├── templates/           # Django templates
│   ├── base.html        # Base layout (header with auth buttons, footer, nav)
│   ├── home.html        # Landing page with role-aware CTAs
│   └── registration/    # Auth templates (login, signup, password reset flow)
└── manage.py
```
