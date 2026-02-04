# Vraa Site Improvements - Implementation Plan

This document provides a detailed implementation plan for the following feature requests:

1. **Notifications for new messages/comments** (email + in-app)
2. **Display name with whitespace support** (while maintaining username best practices)
3. **Family heritage line tags** (4 family lines with visible badges)
4. **Reserved weeks per heritage line** (rolling allocation, calendar visibility)
5. **Security improvements** (corporate network access issues)

---

## Executive Summary

| Phase | Feature | Priority | Effort | Dependencies |
|-------|---------|----------|--------|--------------|
| 1 | Security Improvements | P0 | Low | None |
| 2 | User Profile & Display Names | P1 | Medium | None |
| 3 | Heritage Line System | P1 | Medium | Phase 2 |
| 4 | Reserved Weeks Calendar | P2 | High | Phase 3 |
| 5 | Enhanced Notifications | P2 | Medium | Phase 2 |

**Estimated Total Implementation Time**: 4-6 development sessions

---

## Phase 1: Security Improvements (Corporate Access Fix)

### Problem Analysis

The user reports being blocked from accessing the site on corporate networks with "site not secure" warnings. This is typically caused by:

1. **Missing/Invalid SSL Certificate** - Not the issue here (Heroku provides valid certs)
2. **HSTS Preload Issues** - HSTS is enabled but not preloaded
3. **Mixed Content Warnings** - HTTP resources loaded over HTTPS
4. **Content Security Policy (CSP) Missing** - No CSP headers configured
5. **Certificate Transparency Issues** - Modern browsers require CT logs
6. **Corporate Proxy/Firewall Issues** - May block sites without proper security headers

### Current Security Status (settings.py lines 177-202)

```python
# Already implemented:
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Need to verify
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Implementation Tasks

#### 1.1 Add Missing Security Headers

**File**: `Vraa/settings.py`

```python
# Add to production settings block (if not DEBUG):

# HSTS Preload (allows browser preload list inclusion)
SECURE_HSTS_PRELOAD = True

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cross-Origin headers
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
```

#### 1.2 Add Content Security Policy (CSP)

**Option A**: Use django-csp package (recommended)

```bash
uv add django-csp
```

**File**: `Vraa/settings.py`

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',  # Add after SecurityMiddleware
    # ... rest of middleware
]

# CSP Configuration
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://unpkg.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "https://api.met.no")  # For weather API
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
```

#### 1.3 Add Subresource Integrity (SRI) for CDN Resources

**File**: `main/templates/main/base.html`

Update CDN script/link tags to include SRI hashes:

```html
<!-- Bootstrap CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
      integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
      crossorigin="anonymous">

<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
        crossorigin="anonymous"></script>

<!-- HTMX -->
<script src="https://unpkg.com/htmx.org@1.9.10"
        integrity="sha384-D1Kt99CQMDuVetoL1lrYwg5t+9QdHe7NLX/SoJYkXDFfX37iInKRy5xLSi8nO7UC"
        crossorigin="anonymous"></script>
```

#### 1.4 Update ALLOWED_HOSTS for Production

**File**: `Vraa/settings.py`

```python
if not DEBUG:
    ALLOWED_HOSTS = [
        'vraa.org',
        'www.vraa.org',
        '.herokuapp.com',  # For Heroku review apps
    ]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
```

#### 1.5 Add Permissions-Policy Header

**File**: `Vraa/settings.py` or custom middleware

```python
# Option: Add via django-permissions-policy package
# Or add custom middleware:

class PermissionsPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Permissions-Policy'] = (
            'accelerometer=(), camera=(), geolocation=(), '
            'gyroscope=(), magnetometer=(), microphone=(), '
            'payment=(), usb=()'
        )
        return response
```

### Verification Checklist

After implementation, verify using:

1. **SSL Labs Test**: https://www.ssllabs.com/ssltest/
2. **Security Headers**: https://securityheaders.com/
3. **Mozilla Observatory**: https://observatory.mozilla.org/
4. **Corporate VPN Test**: Access from corporate network

### Files to Modify

| File | Changes |
|------|---------|
| `Vraa/settings.py` | Add security headers, CSP config |
| `main/templates/main/base.html` | Add SRI attributes to CDN resources |
| `pyproject.toml` | Add django-csp dependency |
| `main/middleware.py` | Add PermissionsPolicyMiddleware (optional) |

---

## Phase 2: User Profile & Display Names

### Problem Analysis

Currently, users are identified only by `username`. The user wants:
- Display names with whitespace (e.g., "Rasmus Damgaard" instead of "rdamgaard")
- Keep username as login identifier (no spaces, best practices)
- Display name shown on messages, bookings, and throughout the site

### Current State

- `User` model: Django's built-in (username, email, password)
- `CustomUserCreationForm`: Currently allows spaces in username (should be restricted)
- No `UserProfile` model exists

### Data Model Design

#### 2.1 Create UserProfile Model

**File**: `main/models.py`

```python
class UserProfile(models.Model):
    """
    Extended user profile with display name and additional info.
    Created automatically via signal when User is created.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name shown on messages and bookings (e.g., 'Rasmus Damgaard')"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short bio (optional)"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Profile picture (optional)"
    )
    # Heritage line will be added in Phase 3
    # heritage_line = models.ForeignKey('HeritageLine', ...)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_display_name(self):
        """Return display name if set, otherwise username."""
        return self.display_name if self.display_name else self.user.username

    @property
    def full_display_name(self):
        """Alias for get_display_name() for template convenience."""
        return self.get_display_name()
```

#### 2.2 Create Signal for Auto-Creation

**File**: `main/signals.py` (new file)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
```

**File**: `main/apps.py` (update)

```python
class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.signals  # noqa: F401
```

#### 2.3 Update Registration Form

**File**: `main/forms.py`

```python
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    display_name = forms.CharField(
        max_length=100,
        required=False,
        help_text="Your name as it will appear on messages (e.g., 'Rasmus Damgaard')"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        """Enforce no whitespace in username."""
        username = self.cleaned_data.get('username')
        if username and ' ' in username:
            raise forms.ValidationError(
                "Username cannot contain spaces. Use your display name for spaces."
            )
        return username

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and hasattr(user, 'profile'):
            user.profile.display_name = self.cleaned_data.get('display_name', '')
            user.profile.save()
        return user
```

#### 2.4 Create Profile Edit View

**File**: `main/views.py`

```python
class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Allow users to edit their display name and bio."""
    template_name = 'main/profile_edit.html'
    fields = ['display_name', 'bio']
    success_url = reverse_lazy('main:profile')

    def get_object(self):
        return self.request.user.profile
```

#### 2.5 Update Templates

**Update message display** (`frontpage.html`):
```html
<!-- Before -->
<span class="author">{{ message.author.username }}</span>

<!-- After -->
<span class="author">{{ message.author.profile.get_display_name }}</span>
```

**Update booking display** (`kalender.html`, API response):
```python
# In BookingAPIView
'title': booking.user.profile.get_display_name() if hasattr(booking.user, 'profile') else booking.user.username,
```

#### 2.6 Migration for Existing Users

**File**: `main/management/commands/create_missing_profiles.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create UserProfile for users that do not have one'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        count = 0
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            count += 1
        self.stdout.write(f'Created {count} user profiles')
```

### Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `main/models.py` | Modify | Add UserProfile model |
| `main/signals.py` | Create | Auto-create profile signal |
| `main/apps.py` | Modify | Register signals |
| `main/forms.py` | Modify | Add display_name to registration |
| `main/views.py` | Modify | Add ProfileEditView |
| `main/urls.py` | Modify | Add profile edit URL |
| `main/admin.py` | Modify | Register UserProfile admin |
| `main/templates/main/profile_edit.html` | Create | Profile edit form template |
| `main/templates/main/frontpage.html` | Modify | Use display_name |
| `main/templates/main/kalender.html` | Modify | Use display_name in calendar |
| `main/management/commands/create_missing_profiles.py` | Create | Migration command |

---

## Phase 3: Heritage Line System

### Problem Analysis

The family summerhouse has 4 heritage lines. Each user should:
- Be assigned to a heritage line
- Have a visible badge/tag showing their line
- Line membership displayed on messages and profile

### Data Model Design

#### 3.1 Create HeritageLine Model

**File**: `main/models.py`

```python
class HeritageLine(models.Model):
    """
    Represents one of the 4 family heritage lines.
    Each line has reserved weeks allocated on a rolling basis.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Name of the heritage line (e.g., 'Damgaard-linjen')"
    )
    short_name = models.CharField(
        max_length=20,
        help_text="Short display name for badges (e.g., 'Damgaard')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this heritage line"
    )
    color = models.CharField(
        max_length=7,
        default='#2C5F7C',
        help_text="Hex color code for calendar events (e.g., '#2C5F7C')"
    )
    badge_class = models.CharField(
        max_length=30,
        default='bg-primary',
        help_text="Bootstrap badge class (e.g., 'bg-primary', 'bg-success')"
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )

    # Reserved weeks configuration
    base_weeks = models.JSONField(
        default=list,
        blank=True,
        help_text="Base week numbers for year 0 rotation (e.g., [26, 27])"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Heritage Line'
        verbose_name_plural = 'Heritage Lines'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_reserved_weeks_for_year(self, year):
        """
        Calculate reserved weeks for a specific year using rolling rotation.

        The rotation works as follows:
        - Base year (e.g., 2024) = index 0
        - Each subsequent year, weeks rotate forward by the line's order position

        Example with 4 lines and 2 weeks each:
        - Year 0: Line 1 gets weeks 26-27, Line 2 gets weeks 28-29, etc.
        - Year 1: Line 1 gets weeks 28-29, Line 2 gets weeks 30-31, etc.
        """
        if not self.base_weeks:
            return []

        base_year = 2024  # Reference year for rotation calculation
        year_offset = year - base_year
        total_lines = HeritageLine.objects.count()

        # Each line's weeks rotate by (year_offset * 2 weeks) modulo total weeks
        rotation = (year_offset * len(self.base_weeks)) % (total_lines * len(self.base_weeks))

        # Calculate new weeks based on rotation and line order
        weeks_per_line = len(self.base_weeks)
        start_offset = ((self.order + year_offset) % total_lines) * weeks_per_line

        # Get the actual week numbers
        all_reserved_weeks = list(range(26, 26 + total_lines * weeks_per_line))
        return all_reserved_weeks[start_offset:start_offset + weeks_per_line]
```

#### 3.2 Update UserProfile Model

**File**: `main/models.py` (add to UserProfile)

```python
class UserProfile(models.Model):
    # ... existing fields ...

    heritage_line = models.ForeignKey(
        'HeritageLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text="Family heritage line this user belongs to"
    )

    FAMILY_ROLE_CHOICES = [
        ('member', 'Member'),
        ('elder', 'Elder'),
        ('head', 'Line Head'),
    ]
    family_role = models.CharField(
        max_length=20,
        choices=FAMILY_ROLE_CHOICES,
        default='member',
        help_text="Role within the heritage line"
    )
```

#### 3.3 Create Badge Template Tag

**File**: `main/templatetags/heritage_tags.py`

```python
from django import template
from django.utils.html import format_html

register = template.Library()

@register.simple_tag
def heritage_badge(user):
    """
    Display heritage line badge for a user.
    Usage: {% heritage_badge user %}
    """
    if not hasattr(user, 'profile') or not user.profile.heritage_line:
        return ''

    line = user.profile.heritage_line
    return format_html(
        '<span class="badge {} heritage-badge" title="{}">{}</span>',
        line.badge_class,
        line.name,
        line.short_name
    )


@register.simple_tag
def heritage_color(user):
    """Return heritage line color for calendar events."""
    if not hasattr(user, 'profile') or not user.profile.heritage_line:
        return '#6c757d'  # Default gray
    return user.profile.heritage_line.color
```

#### 3.4 Admin Configuration

**File**: `main/admin.py`

```python
@admin.register(HeritageLine)
class HeritageLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'color', 'order', 'member_count']
    list_editable = ['order']
    ordering = ['order']

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


# Update UserProfileAdmin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_name', 'heritage_line', 'family_role']
    list_filter = ['heritage_line', 'family_role']
    search_fields = ['user__username', 'display_name']
    autocomplete_fields = ['heritage_line']
```

#### 3.5 Initial Data Fixture

**File**: `main/fixtures/heritage_lines.json`

```json
[
    {
        "model": "main.heritageline",
        "pk": 1,
        "fields": {
            "name": "Linje 1",
            "short_name": "L1",
            "description": "Første familielinje",
            "color": "#2C5F7C",
            "badge_class": "bg-primary",
            "order": 0,
            "base_weeks": [26, 27]
        }
    },
    {
        "model": "main.heritageline",
        "pk": 2,
        "fields": {
            "name": "Linje 2",
            "short_name": "L2",
            "description": "Anden familielinje",
            "color": "#5FA8A0",
            "badge_class": "bg-success",
            "order": 1,
            "base_weeks": [28, 29]
        }
    },
    {
        "model": "main.heritageline",
        "pk": 3,
        "fields": {
            "name": "Linje 3",
            "short_name": "L3",
            "description": "Tredje familielinje",
            "color": "#E8A838",
            "badge_class": "bg-warning",
            "order": 2,
            "base_weeks": [30, 31]
        }
    },
    {
        "model": "main.heritageline",
        "pk": 4,
        "fields": {
            "name": "Linje 4",
            "short_name": "L4",
            "description": "Fjerde familielinje",
            "color": "#C75B5B",
            "badge_class": "bg-danger",
            "order": 3,
            "base_weeks": [32, 33]
        }
    }
]
```

### Display Integration

#### Message Board (frontpage.html)
```html
{% load heritage_tags %}

<div class="message-card">
    <div class="message-header">
        <span class="author">{{ message.author.profile.get_display_name }}</span>
        {% heritage_badge message.author %}
        <span class="date">{{ message.created_at|date:"d. M Y" }}</span>
    </div>
    <!-- ... -->
</div>
```

#### Profile Page (profile.html)
```html
{% load heritage_tags %}

<div class="profile-info">
    <h2>{{ user.profile.get_display_name }}</h2>
    {% if user.profile.heritage_line %}
        <div class="heritage-info">
            {% heritage_badge user %}
            <span>{{ user.profile.heritage_line.name }}</span>
            <span class="role">({{ user.profile.get_family_role_display }})</span>
        </div>
    {% endif %}
</div>
```

### Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `main/models.py` | Modify | Add HeritageLine model, update UserProfile |
| `main/admin.py` | Modify | Register HeritageLine admin |
| `main/templatetags/heritage_tags.py` | Create | Badge template tag |
| `main/fixtures/heritage_lines.json` | Create | Initial data |
| `main/templates/main/frontpage.html` | Modify | Add heritage badges |
| `main/templates/main/profile.html` | Modify | Show heritage info |
| `main/static/main/css/style.css` | Modify | Badge styling |

---

## Phase 4: Reserved Weeks Calendar System

### Problem Analysis

Each heritage line has 2 reserved weeks per year. The allocation rotates annually so different lines get different weeks each year. These reserved weeks should be:
- Visible on the calendar
- Color-coded by heritage line
- Shown on the booking page
- Enforced during booking (with appropriate warnings/restrictions)

### Data Model Design

#### 4.1 Create ReservedWeek Model

**File**: `main/models.py`

```python
class ReservedWeek(models.Model):
    """
    Represents a reserved week for a heritage line.
    Can be auto-generated based on rotation rules or manually created.
    """
    heritage_line = models.ForeignKey(
        'HeritageLine',
        on_delete=models.CASCADE,
        related_name='reserved_weeks'
    )
    year = models.PositiveIntegerField(
        help_text="Year this reservation applies to"
    )
    week_number = models.PositiveSmallIntegerField(
        help_text="ISO week number (1-53)"
    )
    start_date = models.DateField(
        help_text="First day of the reserved week (Monday)"
    )
    end_date = models.DateField(
        help_text="Last day of the reserved week (Sunday)"
    )
    is_locked = models.BooleanField(
        default=True,
        help_text="If locked, only members of this line can book during this week"
    )
    notes = models.TextField(
        blank=True,
        help_text="Admin notes about this reservation"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_reservations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reserved Week'
        verbose_name_plural = 'Reserved Weeks'
        ordering = ['year', 'week_number']
        unique_together = ['heritage_line', 'year', 'week_number']
        indexes = [
            models.Index(fields=['year', 'week_number']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.heritage_line.short_name} - Week {self.week_number}, {self.year}"

    def save(self, *args, **kwargs):
        # Auto-calculate dates from year and week number
        if not self.start_date or not self.end_date:
            from datetime import datetime, timedelta
            # ISO week calculation
            jan4 = datetime(self.year, 1, 4)
            start_of_week1 = jan4 - timedelta(days=jan4.weekday())
            self.start_date = start_of_week1 + timedelta(weeks=self.week_number - 1)
            self.end_date = self.start_date + timedelta(days=6)
        super().save(*args, **kwargs)

    @classmethod
    def generate_for_year(cls, year, created_by=None):
        """
        Generate all reserved weeks for a given year based on heritage line rotation.
        """
        from .models import HeritageLine
        created_count = 0

        for line in HeritageLine.objects.all():
            weeks = line.get_reserved_weeks_for_year(year)
            for week_num in weeks:
                _, created = cls.objects.get_or_create(
                    heritage_line=line,
                    year=year,
                    week_number=week_num,
                    defaults={'created_by': created_by}
                )
                if created:
                    created_count += 1

        return created_count

    @classmethod
    def get_reserved_for_date_range(cls, start_date, end_date):
        """Get all reserved weeks overlapping with a date range."""
        return cls.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('heritage_line')
```

#### 4.2 Update Booking Model Validation

**File**: `main/models.py` (update Booking.clean())

```python
class Booking(models.Model):
    # ... existing fields ...

    def clean(self):
        super().clean()

        # Existing validation...

        # Check for reserved week conflicts
        if self.start_date and self.end_date:
            user_line = None
            if hasattr(self.user, 'profile') and self.user.profile.heritage_line:
                user_line = self.user.profile.heritage_line

            conflicting_reservations = ReservedWeek.get_reserved_for_date_range(
                self.start_date, self.end_date
            ).exclude(heritage_line=user_line)

            locked_conflicts = conflicting_reservations.filter(is_locked=True)

            if locked_conflicts.exists():
                conflict = locked_conflicts.first()
                raise ValidationError({
                    'start_date': f"This period overlaps with a reserved week for "
                                  f"{conflict.heritage_line.name} (Week {conflict.week_number}). "
                                  f"Only members of that line can book during this time."
                })
```

#### 4.3 Update Calendar API

**File**: `main/views.py` (update BookingAPIView)

```python
class BookingAPIView(View):
    """JSON API endpoint for calendar events including reserved weeks."""

    def get(self, request):
        # Get date range from request
        start = request.GET.get('start')
        end = request.GET.get('end')

        events = []

        # Add bookings (existing code)
        bookings = Booking.objects.filter(
            status__in=['pending', 'confirmed']
        ).select_related('user__profile__heritage_line')

        for booking in bookings:
            # ... existing booking event code ...
            events.append({
                'id': f'booking-{booking.pk}',
                'title': booking.user.profile.get_display_name() if hasattr(booking.user, 'profile') else booking.user.username,
                'start': booking.start_date.isoformat(),
                'end': (booking.end_date + timedelta(days=1)).isoformat(),
                'color': self.get_booking_color(booking),
                'extendedProps': {
                    'type': 'booking',
                    'status': booking.status,
                    'heritage_line': booking.user.profile.heritage_line.short_name if hasattr(booking.user, 'profile') and booking.user.profile.heritage_line else None,
                }
            })

        # Add reserved weeks
        if start and end:
            start_date = datetime.fromisoformat(start).date()
            end_date = datetime.fromisoformat(end).date()

            reserved_weeks = ReservedWeek.get_reserved_for_date_range(
                start_date, end_date
            )

            for reservation in reserved_weeks:
                events.append({
                    'id': f'reserved-{reservation.pk}',
                    'title': f'{reservation.heritage_line.short_name} - Reserveret',
                    'start': reservation.start_date.isoformat(),
                    'end': (reservation.end_date + timedelta(days=1)).isoformat(),
                    'color': reservation.heritage_line.color,
                    'display': 'background',  # Shows as background event
                    'extendedProps': {
                        'type': 'reserved_week',
                        'heritage_line': reservation.heritage_line.short_name,
                        'week_number': reservation.week_number,
                        'is_locked': reservation.is_locked,
                    }
                })

        return JsonResponse(events, safe=False)

    def get_booking_color(self, booking):
        if booking.status == 'pending':
            return '#ffc107'  # Yellow for pending
        if hasattr(booking.user, 'profile') and booking.user.profile.heritage_line:
            return booking.user.profile.heritage_line.color
        return '#28a745'  # Default green
```

#### 4.4 Create Reserved Week Admin

**File**: `main/admin.py`

```python
@admin.register(ReservedWeek)
class ReservedWeekAdmin(admin.ModelAdmin):
    list_display = ['heritage_line', 'year', 'week_number', 'start_date', 'end_date', 'is_locked']
    list_filter = ['heritage_line', 'year', 'is_locked']
    ordering = ['year', 'week_number']
    date_hierarchy = 'start_date'
    readonly_fields = ['start_date', 'end_date']

    actions = ['generate_next_year']

    def generate_next_year(self, request, queryset):
        from datetime import datetime
        next_year = datetime.now().year + 1
        count = ReservedWeek.generate_for_year(next_year, request.user)
        self.message_user(request, f'Generated {count} reserved weeks for {next_year}')
    generate_next_year.short_description = "Generate reserved weeks for next year"
```

#### 4.5 Management Command

**File**: `main/management/commands/generate_reserved_weeks.py`

```python
from django.core.management.base import BaseCommand
from main.models import ReservedWeek

class Command(BaseCommand):
    help = 'Generate reserved weeks for a specific year'

    def add_arguments(self, parser):
        parser.add_argument('year', type=int, help='Year to generate weeks for')

    def handle(self, *args, **options):
        year = options['year']
        count = ReservedWeek.generate_for_year(year)
        self.stdout.write(
            self.style.SUCCESS(f'Generated {count} reserved weeks for {year}')
        )
```

#### 4.6 Calendar Legend Component

**File**: `main/templates/main/partials/calendar_legend.html`

```html
{% load heritage_tags %}

<div class="calendar-legend card mb-3">
    <div class="card-header">
        <h6 class="mb-0">Kalender forklaring</h6>
    </div>
    <div class="card-body">
        <div class="legend-items">
            {% for line in heritage_lines %}
            <div class="legend-item">
                <span class="legend-color" style="background-color: {{ line.color }};"></span>
                <span class="legend-label">{{ line.name }} (reserveret)</span>
            </div>
            {% endfor %}
            <div class="legend-item">
                <span class="legend-color" style="background-color: #ffc107;"></span>
                <span class="legend-label">Afventer godkendelse</span>
            </div>
        </div>
    </div>
</div>
```

### Rotation System Explanation

The reserved weeks rotate annually. With 4 lines and 2 weeks each:

| Year | Line 1 | Line 2 | Line 3 | Line 4 |
|------|--------|--------|--------|--------|
| 2024 | 26-27 | 28-29 | 30-31 | 32-33 |
| 2025 | 28-29 | 30-31 | 32-33 | 26-27 |
| 2026 | 30-31 | 32-33 | 26-27 | 28-29 |
| 2027 | 32-33 | 26-27 | 28-29 | 30-31 |
| 2028 | 26-27 | 28-29 | 30-31 | 32-33 | (cycle repeats)

### Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `main/models.py` | Modify | Add ReservedWeek model, update Booking validation |
| `main/views.py` | Modify | Update BookingAPIView to include reserved weeks |
| `main/admin.py` | Modify | Add ReservedWeekAdmin |
| `main/management/commands/generate_reserved_weeks.py` | Create | CLI for generating weeks |
| `main/templates/main/kalender.html` | Modify | Add legend, update event rendering |
| `main/templates/main/partials/calendar_legend.html` | Create | Legend component |
| `main/templates/main/booking_form.html` | Modify | Show reservation warnings |
| `main/static/main/css/style.css` | Modify | Legend and reserved week styling |

---

## Phase 5: Enhanced Notifications

### Problem Analysis

The user wants to be notified when new messages or comments are posted. Currently:
- In-app notifications exist for comments on own messages
- Email notifications exist only for booking status changes
- No notification for new messages on the board
- No mention system (@username)

### Implementation Design

#### 5.1 Add New Notification Types

**File**: `main/models.py` (update Notification model)

```python
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'Comment on your message'),
        ('booking_approved', 'Booking approved'),
        ('booking_rejected', 'Booking rejected'),
        ('mention', 'Mentioned in a message'),
        ('reply', 'Reply to your comment'),
        ('new_message', 'New message posted'),  # NEW
        ('booking_reminder', 'Upcoming booking reminder'),  # NEW
    ]
    # ... rest of model unchanged
```

#### 5.2 Create Notification Preferences

**File**: `main/models.py` (add to UserProfile)

```python
class UserProfile(models.Model):
    # ... existing fields ...

    # Notification preferences
    NOTIFICATION_PREF_CHOICES = [
        ('all', 'All notifications'),
        ('mentions_only', 'Mentions only'),
        ('none', 'No email notifications'),
    ]
    email_notification_pref = models.CharField(
        max_length=20,
        choices=NOTIFICATION_PREF_CHOICES,
        default='all',
        help_text="Email notification preference"
    )
    notify_new_messages = models.BooleanField(
        default=True,
        help_text="Receive notifications for all new messages"
    )
    notify_comments = models.BooleanField(
        default=True,
        help_text="Receive notifications for comments on your messages"
    )
```

#### 5.3 Update NotificationService

**File**: `main/services.py`

```python
class NotificationService:
    """Service for creating and sending notifications."""

    @staticmethod
    def notify_new_message(message):
        """
        Notify users who have opted in to new message notifications.
        Excludes the message author.
        """
        from .models import Notification, UserProfile

        # Get users who want new message notifications
        profiles = UserProfile.objects.filter(
            notify_new_messages=True
        ).exclude(user=message.author).select_related('user')

        notifications_created = []
        for profile in profiles:
            notification = Notification.objects.create(
                user=profile.user,
                notification_type='new_message',
                title='Ny besked på opslagstavlen',
                message=f'{message.author.profile.get_display_name()} har skrevet en ny besked: "{message.content[:50]}..."',
                link=f'/#message-{message.pk}'
            )
            notifications_created.append(notification)

            # Send email if user wants it
            if profile.email_notification_pref == 'all':
                NotificationService.send_notification_email(notification)

        return notifications_created

    @staticmethod
    def notify_comment_on_message(message, comment):
        """Enhanced: Notify message author and optionally other commenters."""
        from .models import Notification

        # Skip if commenting on own message
        if message.author == comment.author:
            return None

        notification = Notification.objects.create(
            user=message.author,
            notification_type='comment',
            title='Ny kommentar på din besked',
            message=f'{comment.author.profile.get_display_name()} kommenterede: "{comment.content[:50]}..."',
            link=f'/#message-{message.pk}'
        )

        # Send email if user profile allows
        if hasattr(message.author, 'profile'):
            if message.author.profile.email_notification_pref in ['all', 'mentions_only']:
                if message.author.profile.notify_comments:
                    NotificationService.send_notification_email(notification)

        return notification

    @staticmethod
    def notify_mention(mentioned_user, message_or_comment, author):
        """Notify a user when they are mentioned with @username."""
        from .models import Notification

        if mentioned_user == author:
            return None

        content_preview = message_or_comment.content[:50]
        notification = Notification.objects.create(
            user=mentioned_user,
            notification_type='mention',
            title='Du blev nævnt i en besked',
            message=f'{author.profile.get_display_name()} nævnte dig: "{content_preview}..."',
            link=f'/#message-{message_or_comment.pk if hasattr(message_or_comment, "pk") else message_or_comment.message.pk}'
        )

        # Always email for mentions (unless completely disabled)
        if hasattr(mentioned_user, 'profile'):
            if mentioned_user.profile.email_notification_pref != 'none':
                NotificationService.send_notification_email(notification)

        return notification

    @staticmethod
    def parse_and_notify_mentions(content, author, source_object):
        """
        Parse @username mentions in content and create notifications.
        Returns list of mentioned users.
        """
        import re
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Find all @mentions
        mention_pattern = r'@(\w+)'
        usernames = re.findall(mention_pattern, content)

        mentioned_users = []
        for username in usernames:
            try:
                user = User.objects.get(username__iexact=username)
                NotificationService.notify_mention(user, source_object, author)
                mentioned_users.append(user)
            except User.DoesNotExist:
                pass

        return mentioned_users

    @staticmethod
    def send_notification_email(notification):
        """Send email for a notification."""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string

        if not notification.user.email:
            return False

        subject = notification.title
        html_message = render_to_string('main/email/notification.html', {
            'notification': notification,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://vraa.org'
        })
        plain_message = f"{notification.message}\n\nSe mere: {notification.link}"

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                html_message=html_message,
                fail_silently=True
            )
            return True
        except Exception:
            return False
```

#### 5.4 Create Email Template

**File**: `main/templates/main/email/notification.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2C5F7C; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button { display: inline-block; padding: 10px 20px; background: #5FA8A0; color: white; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Vraa Sommerhus</h1>
        </div>
        <div class="content">
            <h2>{{ notification.title }}</h2>
            <p>{{ notification.message }}</p>
            {% if notification.link %}
            <p><a href="{{ site_url }}{{ notification.link }}" class="button">Se på hjemmesiden</a></p>
            {% endif %}
        </div>
        <div class="footer">
            <p>Du modtager denne email fordi du har tilmeldt dig notifikationer på vraa.org</p>
            <p>Du kan ændre dine notifikationsindstillinger i din <a href="{{ site_url }}/profile/">profil</a></p>
        </div>
    </div>
</body>
</html>
```

#### 5.5 Update Message Create View

**File**: `main/views.py`

```python
class MessageCreateView(LoginRequiredMixin, CreateView):
    # ... existing code ...

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # Notify users about new message
        NotificationService.notify_new_message(self.object)

        # Check for @mentions
        NotificationService.parse_and_notify_mentions(
            self.object.content,
            self.request.user,
            self.object
        )

        return response
```

#### 5.6 Add Notification Preferences to Profile Edit

**File**: `main/forms.py`

```python
class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'email_notification_pref',
            'notify_new_messages',
            'notify_comments',
        ]
        widgets = {
            'email_notification_pref': forms.Select(attrs={'class': 'form-select'}),
            'notify_new_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
```

### Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `main/models.py` | Modify | Add notification types, UserProfile preferences |
| `main/services.py` | Modify | Add notification methods, email sending |
| `main/views.py` | Modify | Trigger notifications on message/comment create |
| `main/forms.py` | Modify | Add NotificationPreferencesForm |
| `main/templates/main/email/notification.html` | Create | Email template |
| `main/templates/main/profile_edit.html` | Modify | Add notification preferences |
| `Vraa/settings.py` | Modify | Add SITE_URL setting |

---

## Implementation Order & Dependencies

```
Phase 1: Security (No dependencies)
    └── Can be done first, immediately improves access

Phase 2: UserProfile & Display Names (No dependencies)
    └── Foundation for Phase 3, 4, and 5

Phase 3: Heritage Lines (Requires Phase 2)
    └── Needs UserProfile model to add heritage_line field

Phase 4: Reserved Weeks (Requires Phase 3)
    └── Needs HeritageLine model for reservation assignment

Phase 5: Enhanced Notifications (Requires Phase 2)
    └── Needs UserProfile for notification preferences
```

### Recommended Implementation Sequence

1. **Day 1**: Phase 1 (Security) - Quick win, solves immediate access problem
2. **Day 2**: Phase 2 (UserProfile) - Foundation for remaining features
3. **Day 3**: Phase 3 (Heritage Lines) - Core family structure
4. **Day 4**: Phase 4 (Reserved Weeks) - Calendar integration
5. **Day 5**: Phase 5 (Notifications) - Communication enhancement

---

## Testing Checklist

### Phase 1: Security
- [ ] Site accessible from corporate network
- [ ] SSL Labs score A or higher
- [ ] Security Headers score A or higher
- [ ] No mixed content warnings
- [ ] CSP not blocking legitimate resources

### Phase 2: UserProfile
- [ ] New users get profile automatically
- [ ] Existing users can create profile via migration command
- [ ] Display name shows on messages
- [ ] Display name shows on bookings
- [ ] Profile edit form works

### Phase 3: Heritage Lines
- [ ] Four heritage lines created
- [ ] Users can be assigned to lines
- [ ] Badge displays on messages
- [ ] Badge displays on profile
- [ ] Admin can manage lines

### Phase 4: Reserved Weeks
- [ ] Reserved weeks generate correctly for year
- [ ] Rotation works across years
- [ ] Reserved weeks show on calendar
- [ ] Booking validation prevents conflicts
- [ ] Legend displays on calendar page

### Phase 5: Notifications
- [ ] New message triggers notifications
- [ ] Comments trigger notifications
- [ ] @mentions work and notify
- [ ] Email notifications send
- [ ] Users can configure preferences

---

## Migration Commands Summary

After implementing all phases:

```bash
# Phase 2: Create UserProfile migration
uv run python manage.py makemigrations main
uv run python manage.py migrate

# Create profiles for existing users
uv run python manage.py create_missing_profiles

# Phase 3: Load heritage line fixtures
uv run python manage.py loaddata heritage_lines

# Phase 4: Generate reserved weeks
uv run python manage.py generate_reserved_weeks 2024
uv run python manage.py generate_reserved_weeks 2025
uv run python manage.py generate_reserved_weeks 2026
```

---

## Configuration Changes Summary

### Environment Variables to Add

```bash
# Heroku config vars
heroku config:set SITE_URL=https://vraa.org

# For email notifications (if not already configured)
heroku config:set EMAIL_HOST_USER=your-email@gmail.com
heroku config:set EMAIL_HOST_PASSWORD=your-app-password
```

### Dependencies to Add

```bash
uv add django-csp  # For Content Security Policy
uv add Pillow      # For avatar images (optional)
```

---

**Document Version**: 1.0
**Created**: 2026-02-04
**Last Updated**: 2026-02-04
