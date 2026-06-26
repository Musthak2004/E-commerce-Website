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
| Run all tests | `python manage.test test --verbosity=2` |
| Test single app | `python manage.py test accounts --verbosity=2` |
| Test cart | `python manage.py test cart --verbosity=2` |
| Test orders | `python manage.py test orders --verbosity=2` |
| Migrate | `python manage.py migrate` |
| Superuser | `python manage.py createsuperuser` |

No linters, formatters, or pre-commit hooks are configured.

## Project structure

- **`django_project/`** — project config (`settings.py`, root `urls.py`)
- **`accounts/`** — `CustomUser` (email-based auth, `USERNAME_FIELD = "email"`), `Profile`
- **`pages/`** — static pages (home, about, contact)
- **`products/`** — product CRUD with seller-ownership enforcement
- **`cart/`** — shopping cart; 52 tests (models, views, URL routing, context processor)
- **`orders/`** — order processing with stock validation; 43 tests (models, views, URL routing, stock validation, ownership isolation)
- **`templates/`** — project-level templates (`base.html`, registration templates)
- **`static/`** — single CSS stylesheet (`css/style.css`, ~2300 lines) and JS (`js/main.js`); uses Font Awesome 6.5.1

## Architecture notes

- **Auth**: `accounts.CustomUser` uses `email` as the unique identifier, not `username`. `AUTH_USER_MODEL = "accounts.CustomUser"` is set in settings.
- **Context processor**: `cart.context_processors.cart_counts` is enabled globally, injecting `cart_count` and `wishlist_count` into all templates.
- **Media**: Uploaded images go to `media/products/`; dev server serves media only when `DEBUG=True`.
- **Frontend**: Gold/warm theme via CSS custom properties. No CSS framework (Bootstrap/Tailwind). Use the `frontend-design` skill (`.agents/skills/frontend-design/SKILL.md`) for UI work.
- **Database**: SQLite (`db.sqlite3`) — pre-seeded with test data and a test account (testuser@gmail.com / test_2004, Seller role).

## Test accounts

| Email | Password | Role |
|-------|----------|------|
| testuser@gmail.com | test_2004 | Seller |
