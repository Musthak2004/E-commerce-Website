# E-commerce Website — Agent Guide

## Quick start

```powershell
.venv\Scripts\activate
python manage.py runserver
```

## Key commands

| Action | Command |
|--------|---------|
| Run dev server | `python manage.py runserver` |
| Run all tests | `$env:DJANGO_SETTINGS_MODULE='django_project.settings'; python -m django test --parallel --verbosity=2` |
| Test single app | `python manage.py test <app> --verbosity=2` |
| After adding/editing models | `python manage.py makemigrations <app>` then `python manage.py migrate` |
| Install dependencies | `.venv\Scripts\pip install -r requirements.txt` |
| Superuser | `python manage.py createsuperuser` |
| Check system | `.venv\Scripts\python manage.py check --deploy` |
| Collect static files | `python manage.py collectstatic` |
| Admin dashboard | Visit `/admin/dashboard/` (staff-only) |

No linters, formatters, or pre-commit hooks are configured.

> **Test gotcha:** `.env` sets `DEBUG=True`. The `if not DEBUG:` block enables `SECURE_SSL_REDIRECT`. **Do NOT set `$env:DEBUG='False'` before running tests** — it causes mass 301 redirect failures. Tests read `DEBUG` from `.env` (which is `True`), keeping SSL redirect off.

## Project structure

- **`django_project/`** — project config (`settings.py`, root `urls.py`)
- **`accounts/`** — `CustomUser` (email-based auth, `USERNAME_FIELD = "email"`), `Profile`, email verification; 47 tests
- **`pages/`** — static pages + contact form + newsletter signup (models/forms/views); 31 tests
- **`products/`** — product CRUD with seller-ownership enforcement, category filtering, sorting, search, tags (M2M); 70 tests
- **`cart/`** — shopping cart + wishlist; 68 tests
- **`orders/`** — order processing with stock validation, user cancellation; 58 tests
- **`coupons/`** — coupon management (code, discount, dates, usage limit); 33 tests
- **`payments/`** — payment processing (Stripe Checkout, webhooks, OneToOne to Order); 32 tests
- **`reviews/`** — product reviews (ForeignKey to User+Product, UniqueConstraint); 26 tests
- **`api/`** — REST API (DRF read-only product endpoint with pagination); 13 tests
- **`templates/`** — project-level templates (`base.html`, registration templates, admin dashboard, breadcrumbs include)
- **`static/`** — single CSS stylesheet (`css/style.css`, ~2500 lines) and JS (`js/main.js`, 203 lines); uses Font Awesome 6.5.1

## Template patterns

- All 29 templates extend `base.html`. Inline `<style>` blocks per page (no global CSS for page-specific styles). Font Awesome icons everywhere.
- URL namespace pattern: `products:product_list`, `cart:cart_detail`, `orders:order_list`, `payments:payment_create`, `reviews:review_create`.
- Back navigation: `<a href="..." class="back-link"><i class="fas fa-arrow-left"></i> Label</a>`.
- Buttons use pill shape (`border-radius: 100px`). Gold accent via CSS custom properties (`--accent`, `--border`, `--bg-card`, etc.).
- Form pattern: `.form-page > .form-card > .styled-form` with `.form-group` per field.

## Architecture notes

- **Auth**: `accounts.CustomUser` uses `email` as the unique identifier, not `username`. `AUTH_USER_MODEL = "accounts.CustomUser"`. Login form labels `username` field as "Email".
- **Context processor**: `cart.context_processors.cart_counts` is enabled globally, injecting `cart_count` and `wishlist_count` into all templates.
- **Media**: Uploaded images go to `media/products/`; dev server serves media only when `DEBUG=True`.
- **Frontend**: Gold/warm theme via CSS custom properties. No CSS framework (Bootstrap/Tailwind). Vanilla JS only, IIFE pattern in `main.js`.
- **Payment flow**: Cart → Create order (stock validation, atomic) → Order detail → Payment create → Payment detail.
- **Review flow**: Product detail (Write a Review) or Order detail (per-item Review) → Review form → Review detail.
- **Database**: SQLite (`db.sqlite3`) — pre-seeded with test data and a test account.

## Test accounts

| Email | Password | Role |
|-------|----------|------|
| testuser@gmail.com | test_2004 | Seller |
