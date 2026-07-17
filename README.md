<div align="center">
  <h1>🛍️ ShopEase</h1>
  <p><strong>Full-featured Django e-commerce platform</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Django-6.0.6-092E20?logo=django&logoColor=white" alt="Django">
    <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/DRF-3.17.1-A30000?logo=django&logoColor=white" alt="DRF">
    <img src="https://img.shields.io/badge/Stripe-15.3.0-008CDD?logo=stripe&logoColor=white" alt="Stripe">
    <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite">
    <img src="https://img.shields.io/badge/451_tests-passing-22C55E" alt="Tests">
    <img src="https://img.shields.io/badge/UI-Design_System-F59E0B" alt="Design System">
  </p>
</div>

A Django e-commerce platform featuring user authentication, product management, shopping cart, order processing, Stripe payment integration, coupon discounts, product reviews, wishlist, email verification, live chat messenger, and a REST API — all wrapped in a warm gold-themed UI with subtle animations and responsive design.

---

## Features

### User Management
- **Email-based authentication** — `CustomUser` model with `USERNAME_FIELD = "email"`; sign in with email, not username
- **Email verification** — Tokenized verification links sent on signup; verification required for order placement
- **Role-based access** — Customer and Seller roles; seller-only product CRUD with ownership enforcement
- **Profile management** — Editable profile with address, contact info, and avatar upload

### Product Catalog
- **Full CRUD for sellers** — Create, update, and delete products with image gallery support
- **Category & tags** — Multi-level organization via categories and many-to-many tags (slug-based URLs)
- **Search & filtering** — Full-text search by name/description, filter by category/tag, sort by price/name/date
- **Pagination** — 12 products per page with page navigation
- **Related products** — Context-aware recommendations on product detail pages (same category or tags)

### Shopping Cart
- **Cart management** — Add, remove, and update item quantities; unique product constraint per cart
- **Wishlist** — Toggle products on/off with a live count badge in the navigation
- **Global context** — Cart and wishlist counts injected globally via a context processor (no per-view boilerplate)
- **Session-based coupons** — Apply discount codes at checkout; validated against date range, usage limits, and minimum order

### Order Processing
- **Atomic checkout** — Stock validation, inventory decrement, coupon application, and order creation inside a single database transaction
- **Status lifecycle** — Pending → Confirmed → Shipped → Delivered → Cancelled (with stock restoration)
- **Order history** — Per-user order list with status badges and detail views showing all line items
- **Email notifications** — Confirmation emails sent on order placement and payment

### Payment Processing (Stripe)
- **Checkout Sessions** — Redirect to Stripe-hosted checkout with itemized line-item pricing
- **Webhook confirmation** — Server-side `checkout.session.completed` event processing with signature verification
- **Multiple methods** — Card, PayPal, Bank Transfer, Cash on Delivery
- **Status tracking** — Pending → Processing → Completed → Failed → Refunded; minimum $0.50 enforced

### Product Reviews
- **Star ratings** — 1–5 rating scale with duplicate-review prevention (unique user + product constraint)
- **Linked access** — Review forms accessible from both product detail pages and order history
- **Aggregated ratings** — Average rating and review count computed as model properties

### Live Chat
- **Buyer-seller messaging** — HTMX-powered live chat with 3-second polling for near-real-time conversation
- **Inbox** — Paginated inbox with last-message preview, unread count badge, and per-conversation detail
- **Rate-limited sending** — 30 messages per minute per user with client + server validation
- **Product-scoped conversations** — Messages tied to a specific product with data preservation on user/product deletion
- **Read-only admin** — Staff can view conversations and messages but not edit them

### REST API
- **Read-only product endpoint** — Django REST Framework `ReadOnlyModelViewSet` with pagination
- **Nested serializers** — Category, tags, average rating, and review count included in responses
- **Throttling** — 100 requests/hour anonymous, 1,000 requests/hour authenticated

### Discount Coupons
- **Flexible types** — Percentage-based (with optional max cap) or fixed-amount discounts
- **Validity rules** — Date range, minimum order amount, and per-code usage limits
- **Session-based application** — Code lookup with uppercase normalization; validated at order creation

### Design & User Experience
- **Warm gold theme** — CSS custom properties design system with pill-shaped buttons, card-based layout, and consistent typography
- **Design system** — Full CSS variable token system (`--accent`, `--bg-card`, `--radius`, `--shadow`, etc.)
- **Animated micro-interactions** — Page entrance fades, staggered product card reveals (30–50ms per card), hover card elevation, button press feedback, back-to-top with scroll detection
- **Toast notifications** — `addToast(message, type)` API for success/error/info notifications with auto-dismiss
- **Image blur-up loading** — Progressive image loading with blurred placeholder transitions
- **Section reveals** — IntersectionObserver-triggered fade-up animations on scroll (`data-animate` attribute)
- **Responsive** — 375px mobile through desktop with systematic breakpoints
- **Accessibility** — Skip-to-content link, focus-visible outlines, `aria-label`/`aria-expanded` controls, `aria-live` regions for dynamic content, `prefers-reduced-motion` support, keyboard navigation
- **Print styles** — Clean print output hiding navigation, overlays, and interactive elements
- **No JavaScript framework** — Vanilla JS (~300 lines) in IIFE pattern; lightweight and dependency-free

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Django 6.0.6, Python 3.13, Django REST Framework 3.17.1 |
| **Frontend** | HTML5, CSS3 (~6,400 lines across 14 files, custom properties, animations), Vanilla JS, Font Awesome 6.5.1 |
| **Typography** | Playfair Display (headings) + Outfit (body) — Google Fonts |
| **Database** | SQLite (development); compatible with PostgreSQL (production) |
| **Auth** | `django.contrib.auth` + custom `AbstractUser`; email-based `USERNAME_FIELD` |
| **Payments** | Stripe Checkout Sessions + Webhooks with signature verification |
| **Storage** | `django-cleanup` (auto-cleanup of orphaned images), Pillow |
| **Static files** | WhiteNoise (compressed + cache-busting manifest) |
| **Config** | `python-decouple` (`.env`-based settings) |
| **Server** | Gunicorn (production); Django dev server (development) |

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
  ├── Wishlist         (OneToOne → user) ── M2M → Product
  ├── Order            (ForeignKey → user)
  │   └── OrderItem    (ForeignKey → order, ForeignKey → product)
  ├── Review           (ForeignKey → user, ForeignKey → product)
  └── Payment          (OneToOne → Order)

Category ──→ Product (ForeignKey ← category)
Tag      ──→ Product (M2M)
Coupon   ──→ Order   (ForeignKey ← coupon, nullable)
ProductImage (ForeignKey → Product)
```

### Key Flows

```
Cart → Create Order (atomic, stock validation, coupon apply)
     → Stripe Checkout Session → User redirected to Stripe
     → Stripe webhook → Payment confirmed → Order confirmed

Product detail / Order detail → Review form → Review created → Rating aggregated

Product detail "Chat with Seller" → Conversation created
     → HTMX polling (3s) → Message sent → Recipient sees in inbox
     → Inbox with unread badge → Conversation view → Mark as read
```

### Design Decisions

- **Context processor** injects `cart_count` and `wishlist_count` globally — no per-view boilerplate
- **Payment flow**: Cart → Create order (atomic, stock validation) → Stripe Checkout → Webhook → Confirm
- **Seller ownership**: All product CRUD views enforce `seller=self.request.user` via queryset filtering
- **Email verification**: Token-based (`uidb64` + token) with `django.utils.http` helpers; required before ordering
- **Coupon application**: Session-based (no database writes until order creation); normalized to uppercase
- **External image URLs**: Products can use remote image URLs (e.g., Unsplash); the `image_url` property handles both local and remote sources
- **Chat data preservation**: Conversation and Message FKs use `SET_NULL` — surviving participants retain their history even if the other user or product is deleted
- **CSS modularization**: Styles split from a single monolithic stylesheet into per-component files (14 files total) for maintainability

---

## Quick Start

```bash
# Clone
git clone https://github.com/Musthak2004/E-commerce-Website.git
cd E-commerce-Website

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your SECRET_KEY, Stripe keys, and email settings
# (Stripe keys are optional for local development — payment flows will error)

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Run the server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** to see the app.

---

## Environment Configuration

All sensitive settings are managed via `.env` using `python-decouple`:

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SECRET_KEY` | — | Yes | Django secret key (`python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`) |
| `DEBUG` | `False` | No | Debug mode; set `True` for development |
| `ALLOWED_HOSTS` | `.pythonanywhere.com,localhost,127.0.0.1` | Yes | Comma-separated allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | — | Yes | Comma-separated trusted origins for POST requests |
| `STRIPE_PUBLISHABLE_KEY` | — | No* | Stripe publishable key (`pk_test_...`) |
| `STRIPE_SECRET_KEY` | — | No* | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | — | No* | Stripe webhook signing secret (`whsec_...`) |

*Required for payment features. The app runs without them; payment flows will error.

Email defaults to the console backend (`django.core.mail.backends.console.EmailBackend`). Configure SMTP for production:

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
| `testuser@gmail.com` | `test_2004` | Seller |

The database (`db.sqlite3`) is pre-seeded with test data including categories, products, and this test account.

---

## Running Tests

The project has **451 tests** across eleven test suites:

| App | Tests | Coverage Highlights |
|-----|-------|--------------------|
| products | 70 | Models, forms, CRUD views, seller permissions, filtering, sorting, search, pagination |
| cart | 68 | Models, add/remove/update views, cart detail, context processor, coupon session integration |
| orders | 58 | Models, atomic order creation (stock + coupon validation), cancellation with stock restore |
| accounts | 47 | CustomUser model, Profile, SignUpForm, email verification, signals, auth URLs |
| coupons | 33 | Coupon model (discount logic, validation), apply/remove views, session management |
| payments | 32 | Payment model, form validation (duplicates, zero-value), Stripe redirect, webhook flow |
| pages | 31 | Models, forms, views (home/about/contact/newsletter), admin dashboard staff-only |
| reviews | 26 | Review model, form validation, duplicate-review prevention, detail view |
| api | 13 | Product list/retrieve, pagination, authentication, serializer field completeness |
| chat | 71 | Models, views, auth, polling, edge cases, HTMX integration |
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
python manage.py test chat --verbosity=2
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
      "category": {"id": 1, "name": "Electronics", "slug": "electronics"},
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

## Project Structure

```
├── accounts/               # User auth, profiles, email verification
│   ├── models.py           # CustomUser (email USERNAME_FIELD), Profile
│   ├── forms.py            # SignUpForm with email duplicate check
│   ├── views.py            # SignUp, EmailVerify, ProfileUpdate
│   ├── signals.py          # Auto-create Profile on user creation
│   └── tests.py            # 47 tests
│
├── cart/                   # Shopping cart + wishlist
│   ├── models.py           # Cart, CartItem, Wishlist
│   ├── views.py            # Add/remove/update cart, wishlist toggle
│   ├── context_processors.py   # Global cart/wishlist counts
│   └── tests.py            # 68 tests
│
├── orders/                 # Order processing
│   ├── models.py           # Order (5 statuses), OrderItem
│   ├── views.py            # Create (atomic), list, detail, cancel
│   └── tests.py            # 58 tests
│
├── coupons/                # Discount coupons
│   ├── models.py           # Coupon (percentage/fixed, date/usage limits)
│   ├── forms.py            # Apply code (uppercase normalization)
│   └── tests.py            # 33 tests
│
├── payments/               # Stripe integration
│   ├── models.py           # Payment (OneToOne Order, Stripe session)
│   ├── forms.py            # Duplicate-payment prevention
│   ├── views.py            # Create session, success, webhook
│   └── tests.py            # 32 tests
│
├── reviews/                # Product reviews
│   ├── models.py           # Review (UniqueConstraint user+product)
│   ├── forms.py            # Rating 1–5, comment validation
│   └── tests.py            # 26 tests
│
├── api/                    # REST API (DRF)
│   ├── serializers.py      # Nested category/tags + computed fields
│   ├── views.py            # ReadOnlyModelViewSet, throttling
│   └── tests.py            # 13 tests
│
├── pages/                  # Static pages + admin dashboard
│   ├── models.py           # ContactMessage, NewsletterSubscriber
│   ├── forms.py            # ContactForm
│   ├── views.py            # Home, About, Contact, Newsletter
│   ├── admin_dashboard.py  # Staff-only stats overview
│   └── tests.py            # 31 tests
│
├── products/               # Product catalog
│   ├── models.py           # Category, Tag, Product, ProductImage
│   ├── forms.py            # Price/stock validation
│   ├── views.py            # CRUD with seller ownership + filters
│   └── tests.py            # 70 tests
│
├── django_project/         # Project configuration
│   ├── settings.py         # All config (16 apps, 8 middleware, Stripe, DRF, logging)
│   ├── urls.py             # Root URLConf + custom error handlers
│   └── wsgi.py             # .env auto-loading, PythonAnywhere-ready
│
├── chat/                   # Live chat messenger
│   ├── models.py           # Conversation, Message with SET_NULL preservation
│   ├── views.py            # Inbox, conversation detail, HTMX polling, mark-read
│   ├── forms.py            # MessageForm with 2000-char limit
│   ├── context_processors.py   # Unread conversation count
│   ├── signals.py          # Cache invalidation on new message
│   ├── urls.py             # Inbox, conversation, polling, mark-read, send
│   ├── admin.py            # Read-only admin for conversations and messages
│   └── tests.py            # 71 tests across 5 test files
│
├── templates/              # 45 templates (all extend base.html)
│   ├── base.html           # Skip-link, nav (auth/badges), search overlay, footer
│   ├── home.html           # Hero, categories, stats
│   ├── about.html          # Company info
│   ├── contact.html        # Contact form
│   ├── errors/             # 400, 403, 404, 500
│   ├── registration/       # Login, signup, password reset (7 templates)
│   └── includes/
│
├── static/
│   ├── css/                # 14 CSS files (6,406 lines total) — design system, components, responsive, animations
│   └── js/main.js          # ~300 lines vanilla JS — nav, search, toasts, animations, chat polling
│
├── .env.example            # Environment variable template
├── AGENTS.md               # AI agent guide
└── manage.py
```

---

## Deployment

Designed for PythonAnywhere with WhiteNoise static file serving:

```bash
# Collect static files
python manage.py collectstatic

# Run production security checks
python manage.py check --deploy

# Start with Gunicorn
gunicorn django_project.wsgi:application --workers=2 --bind=0.0.0.0:8000
```

The project includes production-ready security settings:
- `whitenoise.middleware.WhiteNoiseMiddleware` — compressed, cache-busted static files
- `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*` headers — auto-enabled when `DEBUG=False`
- `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS = "DENY"` — clickjacking protection
- `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE` — secure cookie flags when not in DEBUG
- `CONN_MAX_AGE = 60` — persistent database connections
- `DATA_UPLOAD_MAX_MEMORY_SIZE = 5MB`
- File + console logging with rotation
- `ADMINS` and `SERVER_EMAIL` configured for admin error notifications

### PythonAnywhere Setup

`.env.example` includes PythonAnywhere-ready defaults:

```
ALLOWED_HOSTS=.pythonanywhere.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://*.pythonanywhere.com,http://localhost
```

The `wsgi.py` file auto-loads `.env` via `python-decouple` and configures the Python path for the PythonAnywhere environment.

---

## License

This project is for educational and portfolio purposes.
