# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Activate environment
.venv\Scripts\activate

# Run dev server
python manage.py runserver

# Run all tests
python manage.py test --parallel --verbosity=2

# Run single app tests
python manage.py test accounts --verbosity=2
python manage.py test products --verbosity=2
python manage.py test orders --verbosity=2
python manage.py test cart --verbosity=2
python manage.py test api --verbosity=2
python manage.py test chat --verbosity=2

# Migrations
python manage.py makemigrations <app>
python manage.py migrate

# Other
python manage.py createsuperuser
python manage.py collectstatic
```

No linters, formatters, or pre-commit hooks are configured.

## Architecture overview

Django 6.0.6 e-commerce platform with 11 apps: **accounts**, **products**, **cart**, **orders**, **payments**, **coupons**, **reviews**, **api**, **pages**, **chat**, and the config project **django_project**. SQLite dev database pre-seeded with test data.

### Auth model

`accounts.CustomUser` extends `AbstractUser` with `USERNAME_FIELD = "email"`. Three roles: `CUSTOMER`, `SELLER`, `ADMIN`. Email verification token flow via `uidb64` + `default_token_generator`. `Profile` auto-created via signal. `AUTH_USER_MODEL = "accounts.CustomUser"`.

Key: the login form labels the username field as "Email" in the template — user logs in with email, but the underlying auth uses Django's default where `AuthenticationForm.clean_username` references `USERNAME_FIELD`. The `CustomUser.REQUIRED_FIELDS = ["username"]` means username is collected at signup.

### Key models and relationships

```
CustomUser
 ┣━ Profile (OneToOne, auto-created)
 ┣━ Product (ForeignKey as seller)
 ┣━ Cart (OneToOne) → CartItem (ForeignKey, UniqueConstraint cart+product)
 ┣━ Wishlist (OneToOne) ── M2M ── Product
 ┣━ Order (ForeignKey) → OrderItem (ForeignKey)
 ┣━ Review (ForeignKey, UniqueConstraint user+product)
 ┗━ Payment (OneToOne through Order)

Category ──→ Product (ForeignKey)
Tag ──→ Product (M2M)
Coupon ──→ Order (nullable ForeignKey)
ProductImage (ForeignKey → Product)
```

### Critical data flow

**Cart → Order (atomic)** — `orders.views.create_order` is a `@require_POST` view wrapped in `transaction.atomic()`:
1. Validates stock for every cart item
2. Calculates subtotal, applies coupon discount from session
3. Creates Order, bulk-creates OrderItems
4. Decrements stock, increments coupon `used_count`
5. Deletes all cart items
6. Sends confirmation email (fail-silently)

**Payment flow**: Stripe Checkout Session → User redirected to Stripe → Success URL → `payment_success()` verifies via Stripe API. Async fallback: Stripe webhook handler at `/payments/webhook/` processes `checkout.session.completed` events with signature verification.

### URL namespaces

| Namespace | Base path | Entries |
|-----------|-----------|---------|
| `products:` | `/products/` | list, detail (slug), create, update, delete |
| `cart:` | `/cart/` | detail, add_to_cart, remove_from_cart, update_quantity, toggle_wishlist |
| `orders:` | `/orders/` | create, list, detail, cancel |
| `payments:` | `/payments/` | create, success, detail, webhook |
| `coupons:` | `/coupons/` | apply, remove |
| `reviews:` | `/reviews/` | create (by product_id), detail (pk) |
| `api:` | `/api/` | products list, detail (slug) |
| `chat:` | `/chat/` | inbox, conversation, poll, mark_read, send |
| `accounts:` | `/accounts/` | signup, verify, profile |
| `auth:` | `/accounts/` | login, logout, password reset |
| (pages) | `/` | home, about, contact, newsletter |

### View patterns

- **Product CRUD**: Django class-based views (`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`) with `LoginRequiredMixin` + custom `SellerRequiredMixin` (enforces `user_type == "SELLER"`). Update/delete filter queryset by `seller=self.request.user` for ownership enforcement.
- **Cart, Orders, Coupons, Newsletter**: Function-based views with `@login_required` / `@require_POST` decorators.
- **Chat**: Function-based views for inbox, conversation detail, HTMX polling (`GET`-only), mark-read (`POST`), and send (`POST`), with cache-based rate limiting (30/min/user).
- **Reviews, Pages**: Mix of CBVs and FBVs.
- **API**: DRF `ReadOnlyModelViewSet` with `PageNumberPagination` (12/page, max 48), throttled (100/hr anon, 1000/hr auth).
- **Error handlers**: Custom `handler404`, `handler500`, `handler403`, `handler400` in `django_project/urls.py` rendering `templates/errors/`.

### Template architecture

All 45 templates extend `base.html` (nav with auth badges + cart/wishlist/unread counts, search overlay, footer). Template structure patterns:
- **Product list**: `section.section > .section-header + .shop-toolbar + .product-grid > a.product-card`
- **Product detail**: `section.product-detail-section > .product-detail > .product-detail-gallery + .product-detail-info`
- **Forms**: `section.form-page > .form-card > .styled-form > .form-group`
- **Auth**: `div.auth-page > .auth-card > .auth-card-inner`
- **Cart**: `section.cart-section > .cart-container > .cart-items + .cart-summary`
- **Chat**: Inbox: `section.inbox-section > .inbox-list > a.conversation-card`; Conversation: `section.chat-section > .chat-messages + .chat-form`
- **Animation**: `anim-fadeInUp`, `anim-fadeIn`, `anim-delay-N` classes; `data-animate` attribute on sections triggers IntersectionObserver-based reveal in JS.

### Context processor

`cart.context_processors.cart_counts` is enabled globally — injects `cart_count` and `wishlist_count` into all templates. For unauthenticated users both are `None`.

### Design system (CSS)

14 CSS files in `static/css/` (~6400 lines total) with CSS custom properties (`--accent`, `--bg-card`, `--radius`, `--shadow`, etc.). Split into per-component files (products, cart, chat, auth, reviews, animations, etc.). No CSS framework. Vanilla JS in IIFE pattern (~300 lines). Font Awesome 6.5.1 for icons. Responsive breakpoints from 375px. `prefers-reduced-motion` support.

### Environment config

`python-decouple` reads from `.env` (not committed, use `.env.example` as template). Stripe keys optional for dev. Email defaults to console backend. Security hardening (HSTS, SSL redirect, secure cookies) auto-enables when `DEBUG=False`.

## Gotchas

- **Product.image is an ImageField**. Storing external URLs in it makes `.url` prepend `MEDIA_URL` → broken path. Always use `product.image_url` (property that checks for external URLs) in templates, never `product.image.url`.
- **Test gotcha**: `.env` must keep `DEBUG=True` for tests. Setting `DEBUG=False` mass-fails tests due to `SECURE_SSL_REDIRECT`.
- **Order cancellation** checks if payment exists AND is completed before allowing cancel. Only `PENDING` orders can be cancelled.
- **Coupon application**: session-based (no DB writes until order creation). The coupon `code` field is looked up with `iexact`. Uppercase normalization happens via `CouponApplyForm`.
- **Seller ownership**: `ProductUpdateView` and `ProductDeleteView` override `get_queryset` to filter by `seller=self.request.user` (not just `test_func`).
- **Review uniqueness**: enforced by `UniqueConstraint(fields=["user", "product"])` at DB level PLUS an explicit `exists()` check in `ReviewCreateView.form_valid`.
- **`.env` file uses `DEBUG=False` as default** — for local dev you must edit it to `DEBUG=True`. The repo `.env.example` has `DEBUG=False`.
- **Chat rate limiting**: 30 messages per minute per user via cache. Tests need `CACHES` configured properly or rate-limit checks will fail.
- **Chat null-safe templates**: `conversation.html` renders safely when a sender or buyer/seller user is deleted (FK `SET_NULL`). Test with deleted users and deleted product conversations.
- **Chat context processor**: `chat.context_processors.unread_count` is registered globally. Requires database access on every page render for authenticated users.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
- Author a backlog-ready spec/issue → invoke /spec
