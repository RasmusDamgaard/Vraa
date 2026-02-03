# CLAUDE.md - AI Assistant Documentation for Vraa Project

## Project Overview

**Vraa** is a Django-based web application for a family vacation home. It provides a simple, elegant interface for sharing information about the property, including meeting minutes (referater), statutes (vedtægter), a calendar, and general information.

### Purpose
- Serve as a central hub for family members to access information about the Vraa vacation home
- Display historical meeting minutes and governance documents
- Provide a calendar for booking/scheduling
- Modern, responsive design accessible on all devices

### Tech Stack
- **Framework**: Django 4.x
- **Python Version**: 3.11.4
- **Frontend**: Bootstrap 5.3.3, vanilla CSS with CSS custom properties
- **Database**: SQLite (local), PostgreSQL (production via Heroku)
- **Static Files**: WhiteNoise for serving static assets
- **Deployment**: Heroku-ready with Gunicorn

---

## Repository Structure

```
Vraa/
├── Vraa/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py          # Main settings (environment-aware)
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py              # WSGI entry point
│   └── asgi.py              # ASGI entry point (not actively used)
│
├── main/                    # Primary Django app
│   ├── migrations/          # Database migrations (currently empty)
│   ├── static/main/         # Static assets
│   │   ├── css/
│   │   │   └── style.css    # Main stylesheet with CSS variables
│   │   ├── img/
│   │   │   ├── logo.svg     # Site logo
│   │   │   └── House.JPEG   # Frontpage image
│   │   └── pdfs/
│   │       ├── referater/   # Meeting minutes PDFs (2010-2020)
│   │       └── vedtaegter/  # Statute documents
│   ├── templates/main/      # Django templates
│   │   ├── base.html        # Base template with sidebar navigation
│   │   ├── frontpage.html
│   │   ├── information.html
│   │   ├── referater.html
│   │   ├── vedtaegter.html
│   │   ├── kalender.html
│   │   ├── brugervejledning.html  # User guide (Danish)
│   │   └── admin_vejledning.html  # Admin guide (staff-only)
│   ├── views.py             # Class-based views (TemplateView)
│   ├── urls.py              # App URL patterns
│   ├── models.py            # Models (currently empty)
│   ├── admin.py             # Admin configuration
│   ├── apps.py              # App configuration
│   └── tests.py             # Test cases (to be implemented)
│
├── manage.py                # Django management script
├── pyproject.toml           # Python dependencies (UV/PEP 621)
├── uv.lock                  # Locked dependencies for reproducible builds
├── runtime.txt              # Python version for Heroku
├── Procfile                 # Heroku deployment config
├── db.sqlite3               # Local SQLite database
├── .gitignore               # Git ignore rules
├── README.md                # User-facing documentation
└── TODO.md                  # Feature roadmap and backlog
```

---

## Code Architecture & Conventions

### Design Patterns

#### Class-Based Views
The project uses Django's generic `TemplateView` for all pages:

```python
# main/views.py
class FrontpageView(TemplateView):
    template_name = 'main/frontpage.html'
    extra_context = {'title': 'Frontpage'}
```

This pattern is clean and minimal - perfect for static content pages.

#### Template Inheritance
All pages extend `base.html` which provides:
- Responsive sidebar navigation (desktop) / hamburger menu (mobile)
- Bootstrap 5 integration
- Consistent layout structure
- Active navigation state highlighting

### Styling Conventions

#### CSS Custom Properties (CSS Variables)
The project uses modern CSS with extensive custom properties defined in `style.css`:

```css
:root {
  --primary-blue: #2C5F7C;
  --accent-teal: #5FA8A0;
  --accent-sand: #F4E9D8;
  /* ... etc */
}
```

**Important**: When modifying styles, use the existing CSS variables rather than hardcoding colors.

#### Design System
- **Color Palette**: Nature-inspired (blue, teal, sand) for island/vacation feel
- **Typography**: Inter font family with -apple-system fallbacks
- **Spacing**: Consistent spacing scale (xs/sm/md/lg/xl)
- **Shadows**: Three-tier shadow system (sm/md/lg)
- **Border Radius**: Rounded corners throughout (sm/md/lg)

#### Responsive Design
- Mobile-first approach
- Breakpoints: Mobile (<768px), Tablet (768-992px), Desktop (>992px)
- Hamburger menu on mobile, persistent sidebar on desktop
- Fluid typography scaling

### Python Code Style

#### Type Annotations
The codebase uses `from __future__ import annotations` for forward compatibility:

```python
from __future__ import annotations
from django.views.generic import TemplateView
```

#### Docstrings
Module-level docstrings follow Google style (triple-quoted, concise).

---

## Configuration & Settings

### Environment-Aware Settings

The `settings.py` file adapts based on environment variables:

| Variable | Purpose | Default (Local) | Production |
|----------|---------|-----------------|------------|
| `SECRET_KEY` | Django secret | `'django-insecure-local-dev-key-change-me'` | From Heroku config |
| `DEBUG` | Debug mode | `True` | `False` |
| `DATABASE_URL` | Database connection | SQLite | PostgreSQL (Heroku) |

### Static Files Strategy

**WhiteNoise** is configured for efficient static file serving:
- Compression enabled
- Manifest static storage for cache-busting
- Located in middleware stack after `SecurityMiddleware`

**Static file locations:**
- `STATIC_URL = '/static/'`
- `STATIC_ROOT = BASE_DIR / 'staticfiles'` (collectstatic destination)
- `STATICFILES_DIRS = [BASE_DIR / 'main' / 'static']` (source files)

### Database Configuration

Uses `dj-database-url` for flexible database configuration:
- **Local**: SQLite (`db.sqlite3`)
- **Production**: PostgreSQL via `DATABASE_URL` environment variable

---

## Development Workflow

### Local Setup

#### Using UV

[UV](https://github.com/astral-sh/uv) is a modern, fast Python package manager:

```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Run migrations
uv run python manage.py migrate

# 4. Start development server
uv run python manage.py runserver
# Access at http://127.0.0.1:8000/
```

### Common Commands

```bash
# Run migrations
uv run python manage.py migrate

# Create migrations (if models change)
uv run python manage.py makemigrations

# Collect static files (before deployment)
uv run python manage.py collectstatic --noinput

# Start Django shell
uv run python manage.py shell

# Create superuser for admin
uv run python manage.py createsuperuser

# Run tests
uv run python manage.py test
```

### Adding New Pages

To add a new page:

1. **Create view** in `main/views.py`:
   ```python
   class NewPageView(TemplateView):
       template_name = 'main/newpage.html'
       extra_context = {'title': 'New Page'}
   ```

2. **Add URL pattern** in `main/urls.py`:
   ```python
   path('newpage/', views.NewPageView.as_view(), name='newpage'),
   ```

3. **Create template** at `main/templates/main/newpage.html`:
   ```html
   {% extends 'main/base.html' %}
   {% block content %}
     <h1>New Page Title</h1>
     <p>Content here...</p>
   {% endblock %}
   ```

4. **Add navigation link** in `base.html` sidebar (lines 52-89):
   ```html
   <li class="nav-item">
     <a class="nav-link {% if title == 'New Page' %}active{% endif %}"
        href="{% url 'main:newpage' %}">New Page</a>
   </li>
   ```

### Modifying Styles

**Best practices:**
1. Use existing CSS variables whenever possible
2. Add new variables to `:root` in `style.css` if needed
3. Follow the established naming convention (`--component-property`)
4. Test responsiveness at all breakpoints
5. Maintain mobile-first approach

### Working with Static Files

When adding images, PDFs, or other assets:

```python
# In templates
{% load static %}
<img src="{% static 'main/img/myimage.jpg' %}" alt="Description">
```

Place files in:
- Images: `main/static/main/img/`
- CSS: `main/static/main/css/`
- PDFs: `main/static/main/pdfs/`

**Remember**: Run `python manage.py collectstatic` before deploying.

---

## Deployment

### Heroku Deployment

The project is configured for Heroku with:
- `Procfile`: Specifies `gunicorn Vraa.wsgi`
- `runtime.txt`: Python version (`python-3.11.4`)
- Environment variables set in Heroku dashboard

**Required Heroku Config Vars:**
- `SECRET_KEY`: Django secret key (generate securely)
- `DEBUG`: Set to `False`
- `DATABASE_URL`: Auto-configured by Heroku Postgres addon

### Pre-Deployment Checklist

1. Update `runtime.txt` if Python version changes
2. Run `python manage.py collectstatic`
3. Ensure all migrations are created and committed
4. Test locally with `DEBUG=False`
5. Review `ALLOWED_HOSTS` in `settings.py` (currently set to `['*']` - consider restricting)

### Git Workflow

**Important**: This project uses feature branches prefixed with `claude/`:

```bash
# Current branch naming convention
claude/<feature-description>-<sessionId>

# Example
claude/add-claude-documentation-6msCK
```

**Push protocol:**
- Always use: `git push -u origin <branch-name>`
- Branches must start with `claude/` and match session ID
- Retry on network failures with exponential backoff (2s, 4s, 8s, 16s)

---

## URL Structure

| Path | View | Template | Purpose |
|------|------|----------|---------|
| `/` | `FrontpageView` | `frontpage.html` | Landing page with house image |
| `/information/` | `InformationView` | `information.html` | General property information |
| `/referater/` | `ReferaterView` | `referater.html` | Meeting minutes archive |
| `/vedtaegter/` | `VedtaegterView` | `vedtaegter.html` | Statutes and rules |
| `/kalender/` | `KalenderView` | `kalender.html` | Calendar/booking (login required) |
| `/brugervejledning/` | `BrugervejledningView` | `brugervejledning.html` | User guide in Danish |
| `/admin-vejledning/` | `AdminVejledningView` | `admin_vejledning.html` | Admin guide (staff-only) |
| `/admin/` | Django Admin | N/A | Admin interface |

All URLs (except admin) are defined in `main/urls.py` with namespace `main`.

---

## Key Files Reference

### Critical Configuration Files

- **`Vraa/settings.py`** (116 lines)
  - Environment-aware configuration
  - Database switching (SQLite/PostgreSQL)
  - WhiteNoise middleware setup
  - Static files configuration

- **`Vraa/urls.py`** (20 lines)
  - Root URL dispatcher
  - Includes main app URLs
  - Admin interface registration

### Application Logic

- **`main/views.py`** (26 lines)
  - All view classes
  - Uses `TemplateView` exclusively
  - Sets `title` context for navigation highlighting

- **`main/urls.py`** (16 lines)
  - App namespace: `'main'`
  - Five URL patterns for pages

### Templates

- **`main/templates/main/base.html`** (~145 lines)
  - Master template
  - Bootstrap 5 integration
  - Responsive sidebar/mobile menu
  - Active navigation state logic
  - Help section with user guide link (all users) and admin guide link (staff only via `{% if user.is_staff %}`)

- **`main/templates/main/brugervejledning.html`** - User guide in Danish
  - Sections: Velkommen, Kom i gang, Beskedtavlen, Bookingsystemet, Dokumenter, FAQ
  - Uses Bootstrap accordion for FAQ
  - Cached for 1 hour

- **`main/templates/main/admin_vejledning.html`** - Admin guide (staff-only)
  - Sections: Oversigt, Adgang til Admin, Brugerhåndtering, Bookinghåndtering, Indholdsmoderation, Fejlfinding
  - Not cached (to prevent cache leakage between user permission levels)

### Styling

- **`main/static/main/css/style.css`** (386 lines)
  - CSS custom properties system
  - Mobile-first responsive design
  - Accessibility features (focus states, smooth scrolling)
  - Three breakpoint tiers

### Deployment

- **`pyproject.toml`**
  - PEP 621 compliant project metadata
  - Dependencies: Django 4.x, gunicorn, whitenoise, dj-database-url, psycopg2-binary
  - Used by Heroku for dependency installation via UV
  - Optional dev dependencies section

- **`Procfile`** (1 line)
  - Heroku web dyno configuration

- **`runtime.txt`** (1 line)
  - Python version specification

---

## Important Notes for AI Assistants

### What This Project IS

- A **simple, content-focused website** for a family vacation home
- Built with **Django's generic views** (no complex business logic)
- Uses **static content** displayed through templates
- Configured for **Heroku deployment** with minimal configuration

### What This Project IS NOT

- Not using Django REST Framework or APIs (except simple booking JSON endpoint)
- Not using JavaScript frameworks (Vue/React/etc.)
- Not a complex SPA - uses traditional Django templates with Bootstrap

### Development Principles

1. **Keep it simple**: This is intentionally a minimal Django site
2. **No over-engineering**: Don't add complexity unless explicitly requested
3. **Maintain consistency**: Follow existing patterns (TemplateView, CSS variables)
4. **Mobile-first**: Always test responsive behavior
5. **Accessibility**: Maintain focus states, semantic HTML, ARIA labels

### Common Modifications

#### Adding Content to Existing Pages
Edit the template directly in `main/templates/main/`. Content goes inside `{% block content %}`.

#### Changing Styles
Modify `style.css` using existing CSS variables. Add new variables if needed.

#### Adding Static Assets
Place in appropriate `main/static/main/` subdirectory and reference with `{% static %}`.

#### Database Models
Models exist for Message, Comment, and Booking. If adding new models:
1. Define in `main/models.py`
2. Run `python manage.py makemigrations`
3. Run `python manage.py migrate`
4. Register in `main/admin.py` if needed

#### Staff-Only Pages
To create a page accessible only to staff users:

```python
from django.contrib.auth.mixins import UserPassesTestMixin

class StaffOnlyView(UserPassesTestMixin, TemplateView):
    template_name = 'main/staff_page.html'
    login_url = reverse_lazy('main:login')

    def test_func(self):
        return self.request.user.is_staff
```

**Important**: Do NOT use `@cache_page` decorator on staff-only views, as cached responses could leak to non-staff users. See `AdminVejledningView` for the pattern.

### Testing Approach

Currently no automated tests exist. When adding tests:
- Use Django's `TestCase` in `main/tests.py`
- Test views with `self.client.get()`
- Test template rendering and context
- Example: `response = self.client.get('/')` `self.assertEqual(response.status_code, 200)`

### Security Considerations

- `SECRET_KEY` is environment-aware (safe for local dev)
- `DEBUG` defaults to `True` locally, `False` in production
- `ALLOWED_HOSTS` is currently `['*']` - consider restricting for production
- No user input forms currently (low CSRF risk)
- Static files only - no file uploads

### Performance Notes

- **WhiteNoise** serves static files efficiently with compression
- **SQLite** is fine for this low-traffic site locally
- **PostgreSQL** used in production via Heroku
- No caching configured (likely unnecessary for this use case)

### Language & Localization

- Default language: English (`LANGUAGE_CODE = 'en-us'`)
- Timezone: Europe/Copenhagen (`TIME_ZONE = 'Europe/Copenhagen'`)
- Content is in **Danish** (templates and PDFs)
- `USE_I18N` and `USE_TZ` are enabled

---

## Active TODO Items

See **[TODO.md](TODO.md)** for the complete feature roadmap and backlog.

### High Priority (P1)
- **Password Reset Functionality** - Users have no way to recover forgotten passwords
- **Email Notifications for Booking Status** - Notify users when bookings are approved/rejected

### Medium Priority (P2)
- **User Profile & "My Bookings" Page** - Let users see their booking history
- **Calendar - Click Booking for Details** - Show who made a booking when clicked
- **Calendar Export (ICS)** - Sync with personal calendars
- **In-App Notification System** - Alert users to comments and booking updates
- **Pin Important Messages** - Keep announcements at top of message board
- **Document Management System** - Upload referater/vedtaegter via admin
- **HTMX for Dynamic Interactions** - Better UX without page refreshes

### Low Priority (P3)
- Search functionality, dark mode, weather widget, maintenance requests, PWA support, and more

For full details, effort estimates, and implementation notes, see TODO.md.

---

## Completed TODO Items

Recently completed tasks:
1. ✅ **Update `runtime.txt`** - Updated to Python 3.11.14 per Heroku recommendations
2. ✅ **Migrate to UV package manager** - Added `pyproject.toml` and `uv.lock`; UV is the sole package manager (removed `requirements.txt` for Heroku compatibility)
3. ✅ **Allow users to delete their own messages on the message board** - `MessageDeleteView` implemented with proper permission checks (users can only delete own messages), confirmation dialog via `message_confirm_delete.html` template, and delete button in frontpage UI
4. ✅ **Make the website secure with HTTPS** - Added production security settings including `SECURE_SSL_REDIRECT`, HSTS headers, secure cookies, and restricted `ALLOWED_HOSTS`
5. ✅ **Add functionality for users to comment on message board messages** - Created `Comment` model, `CommentCreateView` and `CommentDeleteView` with proper permissions, updated frontpage to display comments
6. ✅ **Look for performance improvements** - Added database indexes on Message and Comment models, configured local memory caching, optimized queries with `select_related`/`prefetch_related`, added lazy loading for images
7. ✅ **Add booking system to the website** - Created `Booking` model with validation, booking CRUD views, FullCalendar integration, admin approval workflow, and double-booking prevention
8. ✅ **Add on-site documentation pages** - Created `/brugervejledning/` (user guide) accessible to all users with instructions for registration, messages, bookings, and FAQ. Created `/admin-vejledning/` (admin guide) restricted to staff users with Django admin instructions for user approval, booking management, and content moderation. Both pages in Danish with Bootstrap accordion for FAQ sections.

---

## Recent Development History

Key recent changes (from git log):
- **Modern aesthetics**: Redesigned with CSS custom properties, modern color palette
- **Mobile responsiveness**: Hamburger menu, fluid layouts, responsive typography
- **Bootstrap upgrade**: Now using Bootstrap 5.3.3
- **Content migration**: Moved content from old website
- **Heroku deployment**: Configured WhiteNoise, environment variables

---

## Questions? Issues?

For AI assistants encountering unclear patterns:
1. Check this document first
2. Examine similar existing code (e.g., follow TemplateView pattern)
3. Maintain simplicity - this is a deliberately minimal Django site
4. When in doubt, ask the user before adding complexity

For human developers:
- See README.md for setup instructions
- Django documentation: https://docs.djangoproject.com/
- Bootstrap 5 documentation: https://getbootstrap.com/docs/5.3/

---

**Document Version**: 1.2
**Last Updated**: 2026-02-03
**Python Version**: 3.11.4
**Django Version**: 4.x
**Deployment**: Heroku
