# E-commerce Website

A Django-based e-commerce platform with a warm gold-themed UI. Features user authentication, product management, shopping cart, order processing, payment handling, product reviews, and a refined shopping experience with subtle animations.

## Features

- **User Authentication** — Login, signup, password reset (email-based auth with `CustomUser` model)
- **Role-Based Access** — Customer and Seller roles with profile management; redirects for authenticated users
- **Product Management** — Sellers can create, edit, and delete products; product listing with pagination and images
- **Shopping Cart** — Add, remove, update quantities; login-required; cart count badge in header; inline quantity controls
- **Order Processing** — Create orders from cart with stock validation, atomic transactions, order history with status tracking (Pending / Confirmed / Shipped / Delivered / Cancelled)
- **Payment Processing** — Record payments against orders with multiple payment methods and status tracking
- **Coupon System** — Discount coupons with fixed/percentage types, usage limits, validity dates; applied at checkout
- **Product Reviews** — Customers can review products with ratings; duplicate-review prevention, linked from product detail and order detail pages
- **About & Contact Pages** — Static information pages linked in header and footer
- **Responsive Design** — Works on desktop, tablet, and mobile
- **Subtle Animations** — Fade-in/slide-up page entrances, staggered list reveals, image zoom on hover, button press micro-interactions (disabled for reduced-motion preference)

## Tech Stack

- **Backend:** Django 6.0.6, Python 3.13
- **Frontend:** HTML5, CSS3 (custom properties, keyframe animations), vanilla JavaScript, Font Awesome 6.5.1
- **Fonts:** Playfair Display (headings), Outfit (body) — via Google Fonts
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
pip install django pillow stripe

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
│   ├── models.py           # CustomUser (email-based), Profile
│   ├── forms.py            # SignUpForm with duplicate email validation
│   ├── views.py            # SignUpView (redirects authenticated users)
│   ├── admin.py            # CustomUserAdmin, ProfileAdmin
│   ├── signals.py          # Auto-create Profile on user signup
│   └── tests.py            # 33 tests
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
│   ├── views.py            # create_order (atomic, stock validation), order_list, order_detail
│   ├── urls.py             # 3 routes
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
├── pages/                  # Static page routing app
│   ├── views.py            # HomePageView, AboutPageView, ContactPageView
│   ├── urls.py             # Root + /about/ + /contact/
│   └── tests.py            # 4 tests
├── products/               # Product management app
│   ├── models.py           # Category, Product, ProductImage (indexed, ordered)
│   ├── forms.py            # ProductForm (price > 0, stock >= 0 validation)
│   ├── views.py            # CRUD with SellerRequiredMixin (owner-only edit/delete)
│   ├── urls.py             # 5 routes
│   ├── admin.py            # Inline images, list_editable, prepopulated slugs
│   ├── tests.py            # 50 tests
│   └── templates/products/
│       ├── product_list.html          # Grid with staggered card entrance
│       ├── product_detail.html        # Gallery + info with fade-in sections
│       ├── product_form.html          # Styled create/edit form
│       └── product_confirm_delete.html
├── django_project/         # Project configuration
│   ├── settings.py         # Installed apps, templates, auth, media config
│   └── urls.py             # Root URLConf (includes all apps)
├── templates/              # Project-level templates
│   ├── base.html           # Layout: header (auth-aware nav, badges), search overlay, footer
│   ├── home.html           # Hero, featured categories, stats, prompt assistant, CTA
│   ├── about.html          # About page
│   ├── contact.html        # Contact page with form
│   └── registration/       # Login, signup, password reset (6 templates)
├── static/
│   ├── css/style.css       # Complete stylesheet (~2500 lines, animations, responsive)
│   └── js/main.js          # Nav, search, password toggle, alert dismiss, prompt assistant
├── media/products/         # Uploaded product images
└── manage.py
```
