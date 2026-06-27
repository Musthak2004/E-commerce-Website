# E-commerce Website

A Django-based e-commerce platform with a warm gold-themed UI. Features user authentication, product management, shopping cart, order processing, Stripe payment integration, coupon discounts, product reviews, wishlist, email verification, and a refined shopping experience with subtle animations.

## Features

- **User Authentication** — Login, signup, password reset, email verification (token-based, `CustomUser` model with `is_email_verified` field)
- **Role-Based Access** — Customer and Seller roles with profile management; redirects for authenticated users
- **Product Management** — Sellers can create, edit, and delete products; product listing with pagination, images, and search
- **Shopping Cart** — Add, remove, update quantities; login-required; cart count badge in header; inline quantity controls
- **Wishlist** — Toggle products on/off wishlist; wishlist count badge in header
- **Order Processing** — Create orders from cart with stock validation, atomic transactions, order history with status tracking (Pending / Confirmed / Shipped / Delivered / Cancelled), user-initiated cancellation
- **Payment Processing** — Record payments against orders with Stripe Checkout integration, webhook confirmation, and status tracking
- **Coupon System** — Discount coupons with fixed/percentage types, usage limits, validity dates; applied at checkout
- **Product Reviews** — Customers can review products with ratings; duplicate-review prevention, linked from product detail and order detail pages
- **Image Gallery** — Multiple product images with click-to-swap thumbnails
- **Related Products** — Same-category product suggestions on detail page
- **Category Filtering & Sorting** — Filter by category, sort by price/name/date on product list
- **Contact Form** — Working contact form with DB storage and email notification
- **Newsletter Signup** — Email capture with DB storage
- **REST API** — Read-only API for products (Django REST Framework)
- **Admin Dashboard** — Stats overview at `/admin/dashboard/`
- **Responsive Design** — Works on desktop, tablet, and mobile
- **Subtle Animations** — Fade-in/slide-up page entrances, staggered list reveals, image zoom on hover, button press micro-interactions (disabled for reduced-motion preference)

## Tech Stack

- **Backend:** Django 6.0.6, Python 3.13, Django REST Framework 3.17.1
- **Frontend:** HTML5, CSS3 (custom properties, keyframe animations), vanilla JavaScript, Font Awesome 6.5.1
- **Fonts:** Playfair Display (headings), Outfit (body) — via Google Fonts
- **Database:** SQLite (default)
- **Auth:** `django.contrib.auth` with custom `AbstractUser` model (`USERNAME_FIELD = "email"`)
- **Payments:** Stripe Checkout Sessions + Webhooks
- **CI:** GitHub Actions

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Musthak2004/E-commerce-Website.git
cd E-commerce-Website

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

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

The project has **280 tests** across eight apps:

| App | Tests | Coverage |
|-----|-------|----------|
| accounts | 38 | Models, forms, views, signals, URLs, auth flow |
| pages | 4 | URL resolution, template rendering |
| products | 55 | Models, forms, permissions, CRUD workflow, URL routing, search |
| cart | 59 | Models, URL resolution, add/remove/update views, cart detail, context processor, wishlist |
| orders | 48 | Models, URL resolution, create order (stock validation, atomicity, coupons), order detail, order list |
| coupons | 31 | Models (discount logic, validation), forms, views (apply/remove), session management |
| payments | 21 | Models, forms (duplicate-payment prevention), create/detail views, ownership enforcement |
| reviews | 24 | Models, forms (rating/comment validation), create (duplicate-check), detail view |

```bash
# Run all tests
python manage.py test --verbosity=2

# Run specific app tests
python manage.py test accounts --verbosity=2
python manage.py test pages --verbosity=2
python manage.py test products --verbosity=2
python manage.py test cart --verbosity=2
python manage.py test orders --verbosity=2
python manage.py test payments --verbosity=2
python manage.py test reviews --verbosity=2
```

## Project Structure

```
├── accounts/               # User auth app
│   ├── models.py           # CustomUser (email-based, is_email_verified), Profile
│   ├── forms.py            # SignUpForm with duplicate email validation
│   ├── views.py            # SignUpView (sends verification email), VerifyEmailView, ProfileUpdateView
│   ├── urls.py             # signup, profile, verify/<uidb64>/<token>/
│   ├── admin.py            # CustomUserAdmin, ProfileAdmin
│   ├── signals.py          # Auto-create Profile on user signup
│   └── tests.py            # 38 tests
├── cart/                   # Shopping cart app
│   ├── models.py           # Cart, CartItem (UniqueConstraint, MinValueValidator)
│   ├── views.py            # add_to_cart, remove_from_cart, update_quantity, cart_detail
│   ├── urls.py             # 4 routes
│   ├── admin.py            # CartAdmin, CartItemAdmin with search & filters
│   ├── context_processors.py   # cart_count / wishlist_count for nav badge
│   ├── tests.py            # 54 tests
│   └── templates/cart/
│       └── cart_detail.html    # Items with qty controls, order summary, trust badges, empty state
├── orders/                 # Order management app
│   ├── models.py           # Order (5 statuses), OrderItem (with total_price property)
│   ├── views.py            # create_order (atomic, stock validation), order_list, order_detail, cancel_order
│   ├── urls.py             # 4 routes (includes cancel)
│   ├── admin.py            # OrderAdmin with OrderItemInline
│   ├── tests.py            # 41 tests
│   └── templates/orders/
│       ├── order_list.html      # Card-based history with status badges
│       └── order_detail.html    # Contact card, items table, summary panel
├── coupons/                # Coupon/discount app
│   ├── models.py           # Coupon (code, discount type/value, dates, usage limit/used)
│   ├── forms.py            # CouponApplyForm (normalizes to uppercase)
│   ├── views.py            # apply_coupon, remove_coupon (session-based)
│   ├── urls.py             # 2 routes
│   ├── admin.py            # CouponAdmin with filters
│   ├── tests.py            # 31 tests
│   └── templates/coupons/  # (coupon form rendered inside cart detail)
├── payments/               # Payment processing app
│   ├── models.py           # Payment (OneToOneField to Order, status/method tracking)
│   ├── forms.py            # PaymentForm with duplicate-payment & zero-value validation
│   ├── views.py            # PaymentCreateView (Stripe redirect), PaymentDetailView (ownership enforced)
│   ├── urls.py             # 2 routes
│   ├── admin.py            # PaymentAdmin with list filters
│   ├── tests.py            # 21 tests
│   └── templates/payments/
│       ├── payment_form.html    # Checkout with order summary and payment method selection
│       └── payment_detail.html  # Payment receipt with status badge and info cards
├── reviews/                # Product reviews app
│   ├── models.py           # Review (ForeignKey to User + Product, UniqueConstraint, rating validators)
│   ├── forms.py            # ReviewForm with rating/comment validation
│   ├── views.py            # ReviewCreateView (duplicate-check), ReviewDetailView
│   ├── urls.py             # 2 routes
│   ├── admin.py            # ReviewAdmin with user email search
│   ├── tests.py            # 24 tests
│   └── templates/reviews/
│       ├── review_form.html      # Product summary card with styled rating selector
│       └── review_detail.html    # Rating badge, 2-col meta grid, comment card
├── api/                    # REST API
│   ├── serializers.py      # ProductListSerializer, CategorySerializer, TagSerializer
│   ├── views.py            # ProductViewSet (ReadOnlyModelViewSet)
│   └── urls.py             # Router with /products/ endpoint
├── pages/                  # Static page routing app
│   ├── models.py           # ContactMessage, NewsletterSubscriber
│   ├── forms.py            # ContactForm
│   ├── views.py            # Home/About/ContactPageView, newsletter_signup
│   ├── urls.py             # Root + /about/ + /contact/ + /newsletter/
│   ├── admin.py            # ContactMessageAdmin, NewsletterSubscriberAdmin
│   ├── admin_dashboard.py  # admin_dashboard view (staff-only stats)
│   └── tests.py            # 4 tests
├── products/               # Product management app
│   ├── models.py           # Category, Tag, Product (tags M2M), ProductImage (indexed, ordered)
│   ├── forms.py            # ProductForm (price > 0, stock >= 0 validation, tags field)
│   ├── views.py            # CRUD with SellerRequiredMixin, category/tag filtering, sort, search
│   ├── urls.py             # 5 routes
│   ├── admin.py            # Inline images, list_editable, prepopulated slugs, TagAdmin
│   ├── tests.py            # 55 tests
│   └── templates/products/
│       ├── product_list.html          # Grid with staggered card entrance
│       ├── product_detail.html        # Gallery + info with fade-in sections
│       ├── product_form.html          # Styled create/edit form
│       └── product_confirm_delete.html
├── django_project/         # Project configuration
│   ├── settings.py         # Installed apps, templates, auth, media config
│   └── urls.py             # Root URLConf (includes all apps)
├── .github/workflows/      # CI/CD
│   └── ci.yml              # GitHub Actions: test on push/PR
├── templates/              # Project-level templates
│   ├── base.html           # Layout: header (auth-aware nav, badges), search overlay, footer
│   ├── home.html           # Hero, featured categories, stats, prompt assistant, CTA
│   ├── about.html          # About page
│   ├── contact.html        # Contact page with working form
│   ├── admin/
│   │   └── dashboard.html  # Admin dashboard with stats cards
│   ├── includes/
│   │   └── breadcrumbs.html    # Reusable breadcrumb nav
│   └── registration/       # Login, signup, password reset, email verified (7 templates)
├── static/
│   ├── css/style.css       # Complete stylesheet (~2500 lines, animations, responsive)
│   └── js/main.js          # Nav, search, password toggle, alert dismiss, prompt assistant
├── media/products/         # Uploaded product images
└── manage.py
```
