<div align="center">
  <h1>🛍️ ShopEase</h1>
  <p><strong>Full-featured Django e-commerce platform</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Django-6.0.6-092E20?logo=django&logoColor=white" alt="Django">
    <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/DRF-3.17.1-A30000?logo=django&logoColor=white" alt="DRF">
    <img src="https://img.shields.io/badge/Stripe-15.3.0-008CDD?logo=stripe&logoColor=white" alt="Stripe">
    <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite">
    <img src="https://img.shields.io/badge/380_tests-passing-22C55E" alt="Tests">
  </p>
</div>

A Django-based e-commerce platform with a warm gold-themed UI. Features user authentication, product management, shopping cart, order processing, Stripe payment integration, coupon discounts, product reviews, wishlist, email verification, and a refined shopping experience with subtle animations.

---

## Features

### User Management
- **Email-based authentication** — `CustomUser` model with `USERNAME_FIELD = "email"`; no username required for login
- **Token email verification** — Users verify their email via tokenized link before accessing order features
- **Role-based access control** — Customer and Seller roles; seller-only product management
- **Profile management** — Editable profile with address details and avatar upload

### Product Management (Sellers)
- **Full CRUD** — Create, read, update, delete products with ownership enforcement
- **Category & tags** — Products organized by category and many-to-many tags with slug-based URLs
- **Image gallery** — Multiple product images with thumbnail selector on detail page
- **Search & filtering** — Search by name/description, filter by category/tag, sort by price/name/date
- **Pagination** — 12 products per page with paginated browsing

### Shopping
- **Cart** — Add/remove/update quantities; unique product constraint per cart; aggregated total price via DB query
- **Wishlist** — Toggle products on/off; wishlist count badge in navigation
- **Context processor** — Cart and wishlist counts injected globally into all templates

### Orders
- **Atomic order creation** — Stock validation, inventory decrement, and order creation inside a database transaction
- **Status tracking** — Pending → Confirmed → Shipped → Delivered → Cancelled
- **User-initiated cancellation** — Cancel pending orders with automatic stock restoration
- **Order history** — Per-user order list with status badges

### Payments (Stripe)
- **Checkout Sessions** — Redirect to Stripe-hosted checkout with line-item pricing
- **Webhook confirmation** — Server-side `checkout.session.completed` event processing
- **Payment status** — Pending → Processing → Completed → Failed → Refunded
- **Minimum amount** — $0.50 minimum transaction enforced

### Coupons & Discounts
- **Flexible discount types** — Percentage (with optional max cap) or fixed amount
- **Validity rules** — Date range, minimum order amount, usage limits
- **Application** — Code-based, applied at checkout via session; case-insensitive

### Reviews
- **Star ratings** — 1–5 star rating with duplicate-review prevention (unique user + product constraint)
- **Linked access** — Review form accessible from both product detail and order detail pages

### API (REST)
- **Read-only product endpoint** — Django REST Framework `ReadOnlyModelViewSet`
- **Nested serializers** — Category and tag data included; average rating and review count computed
- **Pagination** — Configurable page size (default 12, max 48)
- **Throttling** — 100 req/h anonymous, 1000 req/h authenticated

### Design & UX
- **Warm gold theme** — Custom CSS properties, pill-shaped buttons, card-based layout
- **Subtle animations** — Page entrance fades, staggered product reveals, image zoom on hover, button micro-interactions
- **Responsive** — 375px mobile breakpoint through desktop
- **Accessibility** — Skip-to-content link, focus-visible outlines, reduced-motion support
- **No JavaScript framework** — Vanilla JS in IIFE pattern, lightweight (~200 lines)

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Django 6.0.6, Python 3.13, Django REST Framework 3.17.1 |
| **Frontend** | HTML5, CSS3 (custom properties, keyframes), Vanilla JS, Font Awesome 6.5.1 |
| **Typography** | Playfair Display (headings), Outfit (body) — Google Fonts |
| **Database** | SQLite (development), SQLite/PostgreSQL (production) |
| **Auth** | `django.contrib.auth` + custom `AbstractUser` (`USERNAME_FIELD = "email"`) |
| **Payments** | Stripe Checkout Sessions + Webhooks |
| **Storage** | django-cleanup (auto-cleanup of orphaned images), Pillow |
| **Static files** | WhiteNoise (compressed, cached) |
| **Config** | python-decouple (environment-based settings) |
| **Server** | Gunicorn (production) |

### Dependencies

```
Django==6.0.6
django-cleanup==9.0.0
djangorestframework==3.17.1
gunicorn==25.1.0
pillow==12.2.0
python-decouple==3.8
stripe==15.3.0
whitenoise==6.12.0
```

---

## Architecture

### Entity Relationships

```
CustomUser (AbstractUser)
  ├── Profile          (OneToOne → user)
  ├── Product (seller) (ForeignKey ← seller)
  ├── Cart             (OneToOne → user)
  │   └── CartItem     (ForeignKey → cart, ForeignKey → product)
  ├── Wishlist         (OneToOne → user)
  │   └── M2M → Product
  ├── Order            (ForeignKey → user)
  │   └── OrderItem    (ForeignKey → order, ForeignKey → product)
  ├── Review           (ForeignKey → user, ForeignKey → product)
  └── Payment          (OneToOne → Order)

Category ──→ Product (ForeignKey ← category)
Tag      ──→ Product (M2M)
Coupon   ──→ Order   (ForeignKey ← coupon, nullable)
ProductImage (ForeignKey → Product)
```

### Key Design Decisions

- **Context processor** injects `cart_count` and `wishlist_count` globally — no per-view boilerplate
- **Payment flow**: Cart → Create order (atomic, stock validation) → Stripe Checkout → Webhook → Confirm
- **Review flow**: Product detail or order detail → Review form → Review detail
- **Seller ownership**: All product CRUD views enforce `seller=self.request.user` via queryset filtering
- **Email verification**: Token-based (`uidb64` + token) with `django.utils.http` helpers; verification required before ordering
- **Coupon application**: Session-based (no database writes until order creation); normalized to uppercase

---

## Quick Start

```bash
# Clone
git clone https://github.com/Musthak2004/E-commerce-Website.git
cd E-commerce-Website

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your SECRET_KEY, Stripe keys, and email settings

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Seed test data (optional)
python manage.py loaddata products/fixtures/*.json  # if available

# Run the server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the app.

---

## Configuration

All sensitive settings are managed via `.env` using `python-decouple`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | Django secret key (generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`) |
| `DEBUG` | `False` | Debug mode |
| `ALLOWED_HOSTS` | `.pythonanywhere.com,localhost,127.0.0.1` | Allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | `https://*.pythonanywhere.com,http://localhost` | CSRF trust origins |
| `STRIPE_PUBLISHABLE_KEY` | — | Stripe publishable key (pk_test_...) |
| `STRIPE_SECRET_KEY` | — | Stripe secret key (sk_test_...) |
| `STRIPE_WEBHOOK_SECRET` | — | Stripe webhook signing secret (whsec_...) |

Email settings default to the console backend (`django.core.mail.backends.console.EmailBackend`). Configure SMTP in `.env` for production:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@shopease.com
```

---

## Test Account

| Email | Password | Role |
|-------|----------|------|
| testuser@gmail.com | test_2004 | Seller |

The database is pre-seeded with test data including categories, products, and this test account.

---

## Running Tests

The project has **380 tests** across ten test suites:

| App | Tests | Coverage |
|-----|-------|----------|
| products | 70 | Models (Category/Tag/Product/ProductImage), forms, CRUD views, seller permissions, filtering, sorting, search, pagination |
| cart | 68 | Models (Cart/CartItem/Wishlist), add/remove/update views, cart detail, context processor, coupon-in-cart session |
| orders | 58 | Models, create order (stock validation, atomicity, coupon discount), order detail, list, cancel with stock restore |
| accounts | 47 | CustomUser model, Profile model, SignUpForm, SignUpView, VerifyEmailView, ProfileUpdateView, signals, URLs |
| coupons | 33 | Coupon model (discount logic, validation), forms, apply/remove views, session management, expired/inactive codes |
| payments | 32 | Payment model, PaymentForm (duplicate & zero-value prevention), create/detail/success views, ownership, URL resolves |
| pages | 31 | Models (ContactMessage, NewsletterSubscriber), forms, views (home/about/contact/newsletter/dashboard) |
| reviews | 26 | Review model, ReviewForm (rating/comment validation), create (duplicate-check), detail view, URL resolves |
| api | 13 | Product list/retrieve endpoints, pagination, authentication, serializer field completeness |
| django_project | 2 | Custom error handlers (403, 404) |

```bash
# Run all tests
python manage.py test --verbosity=2

# Run in parallel (8 workers)
python manage.py test --parallel --verbosity=2

# Run specific app
python manage.py test accounts --verbosity=2
python manage.py test products --verbosity=2
python manage.py test orders --verbosity=2
```

---

## API Reference

### `GET /api/products/`

Returns a paginated list of available products.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Items per page (default: 12, max: 48) |

**Response:**

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Wireless Headphones",
      "slug": "wireless-headphones",
      "description": "Premium wireless headphones with noise cancellation.",
      "price": "79.99",
      "stock": 15,
      "is_available": true,
      "image": "http://localhost:8000/media/products/headphones.jpg",
      "category": {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics"
      },
      "tags": [
        {"id": 1, "name": "Wireless", "slug": "wireless"},
        {"id": 2, "name": "Audio", "slug": "audio"}
      ],
      "average_rating": 4.2,
      "review_count": 5,
      "created_at": "2026-06-20T10:30:00Z"
    }
  ]
}
```

### `GET /api/products/<slug:slug>/`

Returns a single product by slug.

---

## Deployment

Designed for PythonAnywhere (free plan) with WhiteNoise for static files:

```bash
# Collect static files
python manage.py collectstatic

# Run production checks
python manage.py check --deploy

# Start with Gunicorn
gunicorn django_project.wsgi:application --workers=2 --bind=0.0.0.0:8000
```

The project includes production-ready settings:
- `whitenoise.middleware.WhiteNoiseMiddleware` for static file serving (compressed + cached)
- `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*` headers (enabled when `DEBUG=False`)
- `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS = "DENY"`
- `CONN_MAX_AGE = 60` for persistent database connections
- `DATA_UPLOAD_MAX_MEMORY_SIZE = 5MB`
- File + console logging with rotation
- `ADMINS` and `SERVER_EMAIL` configured for error notifications

### Environment Setup for PythonAnywhere

`.env.example` includes PythonAnywhere-ready defaults:
```
ALLOWED_HOSTS=.pythonanywhere.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://*.pythonanywhere.com,http://localhost
```

The `wsgi.py` file auto-loads `.env` and configures the Python path for PythonAnywhere.

---

## Project Structure

```
├── accounts/               # User authentication (CustomUser, Profile, email verification)
│   ├── models.py           # CustomUser (email-based USERNAME_FIELD), Profile (OneToOne)
│   ├── forms.py            # SignUpForm with duplicate email check
│   ├── views.py            # SignUpView (welcome email), VerifyEmailView, ProfileUpdateView
│   ├── urls.py             # signup/, profile/, verify/<uidb64>/<token>/
│   ├── admin.py            # CustomUserAdmin, ProfileAdmin
│   ├── signals.py          # Auto-create Profile on user creation
│   └── tests.py            # 47 tests
├── cart/                   # Shopping cart + wishlist
│   ├── models.py           # Cart (OneToOne), CartItem (UniqueConstraint), Wishlist (M2M)
│   ├── views.py            # add/remove/update cart, cart_detail, toggle_wishlist
│   ├── urls.py             # 5 routes
│   ├── admin.py            # CartAdmin, CartItemAdmin
│   ├── context_processors.py   # cart_count, wishlist_count (global template injection)
│   ├── tests.py            # 68 tests
│   └── templates/cart/
├── orders/                 # Order processing
│   ├── models.py           # Order (5 statuses, db_index on created_at), OrderItem
│   ├── views.py            # create (atomic), list, detail, cancel (stock restore)
│   ├── urls.py             # 4 routes
│   ├── admin.py            # OrderAdmin with inline items
│   ├── tests.py            # 58 tests
│   └── templates/orders/
├── coupons/                # Discount coupons
│   ├── models.py           # Coupon (percentage/fixed, dates, usage limits, validation)
│   ├── forms.py            # CouponApplyForm (uppercase normalization)
│   ├── views.py            # apply/remove (session-based)
│   ├── urls.py             # 2 routes
│   ├── admin.py            # CouponAdmin with filters
│   ├── tests.py            # 33 tests
├── payments/               # Stripe payment processing
│   ├── models.py           # Payment (OneToOne Order, Stripe session ID, status)
│   ├── forms.py            # PaymentForm (duplicate-payment prevention)
│   ├── views.py            # create (Stripe redirect), success (webhook verify), detail, webhook
│   ├── urls.py             # 4 routes
│   ├── admin.py            # PaymentAdmin
│   ├── tests.py            # 32 tests
│   └── templates/payments/
├── reviews/                # Product reviews
│   ├── models.py           # Review (UniqueConstraint user+product, rating 1-5)
│   ├── forms.py            # ReviewForm
│   ├── views.py            # ReviewCreateView (duplicate-guard), ReviewDetailView
│   ├── urls.py             # 2 routes
│   ├── admin.py            # ReviewAdmin
│   ├── tests.py            # 26 tests
│   └── templates/reviews/
├── api/                    # REST API (DRF)
│   ├── serializers.py      # ProductListSerializer with nested category/tags + computed fields
│   ├── views.py            # ProductViewSet (ReadOnly, slug lookup, pagination)
│   ├── urls.py             # /products/ endpoint (DefaultRouter)
│   └── tests.py            # 13 tests
├── pages/                  # Static pages + admin dashboard
│   ├── models.py           # ContactMessage, NewsletterSubscriber
│   ├── forms.py            # ContactForm
│   ├── views.py            # Home/About/Contact views, newsletter_signup
│   ├── urls.py             # /, /about/, /contact/, /newsletter/
│   ├── admin.py            # ContactMessageAdmin, NewsletterSubscriberAdmin
│   ├── admin_dashboard.py  # Staff-only stats view
│   └── tests.py            # 31 tests
├── products/               # Product catalog
│   ├── models.py           # Category, Tag, Product (MinValueValidator price), ProductImage
│   ├── forms.py            # ProductForm (price > 0 validation, tags CheckboxSelectMultiple)
│   ├── views.py            # CRUD with seller ownership + filtering/sorting/search
│   ├── urls.py             # 5 routes (slug-based)
│   ├── admin.py            # ProductAdmin with inline images + list_editable
│   ├── tests.py            # 70 tests
│   └── templates/products/
├── django_project/         # Project configuration
│   ├── settings.py         # All config: apps, middleware, auth, DRF, Stripe, security, logging
│   ├── urls.py             # Root URLConf (all URL includes + custom error handlers)
│   ├── wsgi.py             # WSGI with .env auto-loading and sys.path setup for PA
│   └── tests.py            # Custom error handler tests (403, 404)
├── templates/              # Project-level templates (29 total, all extend base.html)
│   ├── base.html           # Layout: skip-link, nav (auth-aware, badges), search overlay, footer
│   ├── home.html           # Hero, featured categories, stats
│   ├── about.html          # Company info
│   ├── contact.html        # Contact form
│   ├── errors/             # 400, 403, 404, 500 error pages
│   ├── admin/dashboard.html    # Stats overview
│   ├── registration/       # Login, signup, password reset (7 templates)
│   └── includes/breadcrumbs.html
├── static/
│   ├── css/style.css       # Complete stylesheet (~2500 lines): animations, responsive, gold theme
│   └── js/main.js          # Vanilla JS (203 lines): nav, search, alerts, animations, form loading
├── media/products/         # Uploaded product images
├── .env.example            # Environment variable template
├── AGENTS.md               # AI agent guide
└── manage.py
```

---

## License

This project is for educational and portfolio purposes.
