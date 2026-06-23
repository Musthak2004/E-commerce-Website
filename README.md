# E-commerce Website

A Django-based e-commerce platform with a clean, minimal UI. Features user authentication, product management, and a refined shopping experience.

## Features

- **User Authentication** — Login, signup, password reset (email-based auth with `CustomUser` model)
- **Responsive Design** — Works on desktop, tablet, and mobile
- **Clean UI** — Warm minimal aesthetic with gold accents, Playfair Display + Outfit fonts
- **Account Types** — Customer and Seller roles with profile management

## Tech Stack

- **Backend:** Django 6.0, Python 3.13
- **Frontend:** HTML5, CSS3, vanilla JavaScript
- **Database:** SQLite (default)
- **Auth:** `django.contrib.auth` with custom `AbstractUser` model

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/E-commerce-Website.git
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
│   ├── models.py        # CustomUser, Profile
│   ├── forms.py         # SignUpForm
│   ├── views.py         # SignUpView
│   ├── tests.py         # 33 tests (models, forms, views, signals, URLs)
│   └── signals.py       # Auto-create Profile on user signup
├── pages/               # Page routing app
│   ├── views.py         # HomePageView
│   ├── urls.py          # Root URL routing
│   └── tests.py         # 4 tests (URLs, templates)
├── django_project/      # Project settings and URLs
├── static/
│   ├── css/style.css    # Complete stylesheet
│   └── js/main.js       # Frontend interactions
├── templates/           # Django templates
│   ├── base.html        # Base layout (header, footer, nav)
│   ├── home.html        # Landing page
│   └── registration/    # Auth templates (login, signup, password reset)
└── manage.py
```
