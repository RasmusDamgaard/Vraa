# Vraa Project - Comprehensive Implementation Plan

**Document Version**: 1.0
**Created**: 2026-02-03
**Purpose**: Technical implementation guide for all roadmap features

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Implementation Phases](#implementation-phases)
3. [Phase 1: Security & Authentication](#phase-1-security--authentication)
4. [Phase 2: User Experience Enhancements](#phase-2-user-experience-enhancements)
5. [Phase 3: Communication Features](#phase-3-communication-features)
6. [Phase 4: Administrative Tools](#phase-4-administrative-tools)
7. [Phase 5: Quality of Life Features](#phase-5-quality-of-life-features)
8. [Phase 6: Technical Improvements](#phase-6-technical-improvements)
9. [Database Schema Changes](#database-schema-changes)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Considerations](#deployment-considerations)

---

## Executive Summary

This document provides a detailed technical implementation plan for all features in the Vraa vacation home website roadmap. Features are organized into logical phases based on dependencies and priorities.

### Current System State

**Existing Models:**
- `Message` - Message board posts with author, content, timestamps
- `Comment` - Comments on messages
- `Booking` - Vacation home bookings with status workflow (pending/confirmed/cancelled)

**Existing Views:**
- Static pages: Information, Referater, Vedtaegter
- Dynamic: FrontpageView (ListView), KalenderView (LoginRequired)
- CRUD: Message, Comment, Booking create/update/delete
- Auth: Login, Logout, Register (with admin approval)
- API: BookingAPIView (JSON for FullCalendar)

**Current Infrastructure:**
- Django 4.x with class-based views
- Bootstrap 5.3.3 for UI
- FullCalendar 6.x for calendar
- WhiteNoise for static files
- Email configured (console backend in dev)
- SQLite locally, PostgreSQL on Heroku

---

## Implementation Phases

| Phase | Priority | Focus Area | Estimated Complexity |
|-------|----------|------------|---------------------|
| 1 | P1 | Security & Authentication | Low-Medium |
| 2 | P1-P2 | User Experience Enhancements | Low-Medium |
| 3 | P2 | Communication Features | Medium |
| 4 | P2-P3 | Administrative Tools | Medium |
| 5 | P3 | Quality of Life Features | Medium |
| 6 | P2-P3 | Technical Improvements | Medium-High |

---

## Phase 1: Security & Authentication

### 1.1 Require Login for Entire Site (P1)

**Goal**: All content visible only to authenticated family members.

#### Implementation Strategy: Middleware Approach (Recommended)

**New File: `main/middleware.py`**

```python
"""
Middleware for site-wide authentication requirements.
"""
from __future__ import annotations

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """
    Middleware that requires authentication for all views except
    explicitly exempted URLs.
    """

    EXEMPT_URLS = [
        '/login/',
        '/register/',
        '/brugervejledning/',  # Keep user guide public
        '/admin/',  # Django admin has its own auth
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info

            # Check if path is exempt
            is_exempt = any(
                path.startswith(exempt_url)
                for exempt_url in self.EXEMPT_URLS
            )

            # Also exempt static files
            if path.startswith('/static/'):
                is_exempt = True

            if not is_exempt:
                return redirect(f"{reverse('main:login')}?next={path}")

        return self.get_response(request)
```

**Settings Changes (`Vraa/settings.py:43-53`):**

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'main.middleware.LoginRequiredMiddleware',  # Add after AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Files to Modify:**
- Create: `main/middleware.py`
- Modify: `Vraa/settings.py` (line ~47)
- Modify: `main/templates/main/brugervejledning.html` (add note about login requirement)

**Testing:**
1. Access any page without login → redirected to login
2. Login → access all pages
3. Exempt URLs accessible without login
4. `?next=` parameter works correctly

---

### 1.2 Password Reset Functionality (P1)

**Goal**: Allow users to reset forgotten passwords via email.

#### Implementation Details

**URL Configuration (`main/urls.py`):**

Add these URL patterns:

```python
from django.contrib.auth import views as auth_views

urlpatterns += [
    # Password reset flow
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='main/password_reset.html',
             email_template_name='main/password_reset_email.html',
             subject_template_name='main/password_reset_subject.txt',
             success_url=reverse_lazy('main:password_reset_done'),
             extra_context={'title': 'Nulstil adgangskode'},
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='main/password_reset_done.html',
             extra_context={'title': 'E-mail sendt'},
         ),
         name='password_reset_done'),

    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='main/password_reset_confirm.html',
             success_url=reverse_lazy('main:password_reset_complete'),
             extra_context={'title': 'Vælg ny adgangskode'},
         ),
         name='password_reset_confirm'),

    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='main/password_reset_complete.html',
             extra_context={'title': 'Adgangskode nulstillet'},
         ),
         name='password_reset_complete'),
]
```

**New Templates Required:**

1. `main/templates/main/password_reset.html` - Form to enter email
2. `main/templates/main/password_reset_done.html` - Confirmation email sent
3. `main/templates/main/password_reset_email.html` - Email body (plain text)
4. `main/templates/main/password_reset_subject.txt` - Email subject line
5. `main/templates/main/password_reset_confirm.html` - New password form
6. `main/templates/main/password_reset_complete.html` - Success message

**Template Example (`password_reset.html`):**

```html
{% extends 'main/base.html' %}

{% block content %}
<div class="auth-form-container">
    <h1>Glemt adgangskode?</h1>
    <p>Indtast din e-mailadresse, og vi sender dig et link til at nulstille din adgangskode.</p>

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label for="id_email" class="form-label">E-mail</label>
            {{ form.email }}
        </div>
        <button type="submit" class="btn btn-primary w-100">Send nulstillingslink</button>
    </form>

    <p class="mt-3 text-center">
        <a href="{% url 'main:login' %}">Tilbage til log ind</a>
    </p>
</div>
{% endblock %}
```

**Login Template Modification (`main/templates/main/login.html`):**

Add link below the login form:

```html
<p class="mt-2">
    <a href="{% url 'main:password_reset' %}">Glemt adgangskode?</a>
</p>
```

**Email Configuration for Production:**

Already configured in `settings.py:129-138`. Ensure Heroku config vars are set:
- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST=smtp.sendgrid.net`
- `EMAIL_PORT=587`
- `EMAIL_USE_TLS=True`
- `EMAIL_HOST_USER=apikey`
- `EMAIL_HOST_PASSWORD=<SendGrid API key>`

**Files to Create/Modify:**
- Modify: `main/urls.py` (add 4 URL patterns)
- Modify: `main/templates/main/login.html` (add forgot password link)
- Create: 6 new templates in `main/templates/main/`

---

### 1.3 Email Notifications for Booking Status (P1)

**Goal**: Notify users when their booking is approved or rejected.

#### Implementation Details

**Admin Action Override (`main/admin.py`):**

```python
from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Booking, Message, Comment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['status', 'start_date']
    search_fields = ['user__username', 'notes']
    date_hierarchy = 'start_date'
    actions = ['approve_bookings', 'reject_bookings']

    def save_model(self, request, obj, form, change):
        """Send notification email when status changes."""
        if change:  # Only for updates, not new objects
            old_obj = Booking.objects.get(pk=obj.pk)
            status_changed = old_obj.status != obj.status
        else:
            status_changed = False

        super().save_model(request, obj, form, change)

        if status_changed and obj.user.email:
            self._send_status_notification(obj)

    def _send_status_notification(self, booking):
        """Send email notification about booking status change."""
        if booking.status == 'confirmed':
            subject = 'Din booking er godkendt - Vraa'
            message = (
                f'Hej {booking.user.username},\n\n'
                f'Din booking er blevet godkendt!\n\n'
                f'Detaljer:\n'
                f'- Ankomst: {booking.start_date.strftime("%d. %B %Y")}\n'
                f'- Afrejse: {booking.end_date.strftime("%d. %B %Y")}\n'
                f'- Antal dage: {booking.duration_days}\n\n'
                f'Vi glæder os til at se dig!\n\n'
                f'Venlig hilsen,\nVraa'
            )
        elif booking.status == 'cancelled':
            subject = 'Din booking er afvist - Vraa'
            message = (
                f'Hej {booking.user.username},\n\n'
                f'Desværre er din booking blevet afvist.\n\n'
                f'Booking detaljer:\n'
                f'- Ankomst: {booking.start_date.strftime("%d. %B %Y")}\n'
                f'- Afrejse: {booking.end_date.strftime("%d. %B %Y")}\n\n'
                f'Kontakt venligst en administrator for mere information.\n\n'
                f'Venlig hilsen,\nVraa'
            )
        else:
            return  # Don't send for 'pending' status

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.user.email],
                fail_silently=True,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Failed to send booking notification: {e}')

    @admin.action(description='Godkend valgte bookinger')
    def approve_bookings(self, request, queryset):
        """Bulk approve bookings."""
        for booking in queryset.filter(status='pending'):
            booking.status = 'confirmed'
            booking.save()
            if booking.user.email:
                self._send_status_notification(booking)
        self.message_user(request, f'{queryset.count()} booking(er) godkendt.')

    @admin.action(description='Afvis valgte bookinger')
    def reject_bookings(self, request, queryset):
        """Bulk reject bookings."""
        for booking in queryset.filter(status='pending'):
            booking.status = 'cancelled'
            booking.save()
            if booking.user.email:
                self._send_status_notification(booking)
        self.message_user(request, f'{queryset.count()} booking(er) afvist.')
```

**Files to Modify:**
- Modify: `main/admin.py` (enhance BookingAdmin)

---

## Phase 2: User Experience Enhancements

### 2.1 User Profile & "My Bookings" Page (P2)

**Goal**: Let users see their booking history and profile information.

#### Implementation Details

**New View (`main/views.py`):**

```python
class ProfileView(LoginRequiredMixin, TemplateView):
    """Display user profile with their bookings."""

    template_name = 'main/profile.html'
    extra_context = {'title': 'Min profil'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Separate bookings by time and status
        today = timezone.now().date()

        context['upcoming_bookings'] = Booking.objects.filter(
            user=user,
            end_date__gte=today,
            status__in=['pending', 'confirmed'],
        ).select_related('user').order_by('start_date')

        context['past_bookings'] = Booking.objects.filter(
            user=user,
            end_date__lt=today,
        ).select_related('user').order_by('-start_date')[:10]

        context['cancelled_bookings'] = Booking.objects.filter(
            user=user,
            status='cancelled',
        ).select_related('user').order_by('-created_at')[:5]

        # User statistics
        context['total_bookings'] = Booking.objects.filter(user=user).count()
        context['total_messages'] = Message.objects.filter(author=user).count()
        context['total_comments'] = Comment.objects.filter(author=user).count()

        return context
```

**URL Pattern (`main/urls.py`):**

```python
path('profil/', views.ProfileView.as_view(), name='profile'),
```

**New Template (`main/templates/main/profile.html`):**

```html
{% extends 'main/base.html' %}

{% block content %}
<div class="profile-container">
    <h1>Min profil</h1>

    <div class="card mb-4">
        <div class="card-body">
            <h5 class="card-title">Kontoinformation</h5>
            <p><strong>Brugernavn:</strong> {{ user.username }}</p>
            <p><strong>E-mail:</strong> {{ user.email|default:"Ikke angivet" }}</p>
            <p><strong>Medlem siden:</strong> {{ user.date_joined|date:"d. F Y" }}</p>
        </div>
    </div>

    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h3>{{ total_bookings }}</h3>
                    <p class="text-muted">Bookinger</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h3>{{ total_messages }}</h3>
                    <p class="text-muted">Beskeder</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h3>{{ total_comments }}</h3>
                    <p class="text-muted">Kommentarer</p>
                </div>
            </div>
        </div>
    </div>

    <h2>Kommende bookinger</h2>
    {% if upcoming_bookings %}
    <div class="list-group mb-4">
        {% for booking in upcoming_bookings %}
        <div class="list-group-item d-flex justify-content-between align-items-center">
            <div>
                <strong>{{ booking.start_date|date:"d. M Y" }} - {{ booking.end_date|date:"d. M Y" }}</strong>
                <br>
                <small class="text-muted">{{ booking.duration_days }} dage</small>
            </div>
            <div>
                <span class="badge {% if booking.status == 'confirmed' %}bg-success{% else %}bg-warning text-dark{% endif %}">
                    {{ booking.get_status_display }}
                </span>
                {% if booking.status == 'pending' %}
                <a href="{% url 'main:booking_update' booking.pk %}" class="btn btn-sm btn-outline-secondary ms-2">Rediger</a>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <p class="text-muted">Ingen kommende bookinger.</p>
    {% endif %}

    <h2>Tidligere bookinger</h2>
    {% if past_bookings %}
    <div class="list-group mb-4">
        {% for booking in past_bookings %}
        <div class="list-group-item">
            <strong>{{ booking.start_date|date:"d. M Y" }} - {{ booking.end_date|date:"d. M Y" }}</strong>
            <span class="badge bg-secondary ms-2">Afsluttet</span>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <p class="text-muted">Ingen tidligere bookinger.</p>
    {% endif %}
</div>
{% endblock %}
```

**Navigation Update (`main/templates/main/base.html`):**

Add to sidebar navigation (after Kalender, around line 99):

```html
{% if user.is_authenticated %}
<li class="nav-item">
  <a class="nav-link {% if title == 'Min profil' %}active{% endif %}"
     href="{% url 'main:profile' %}">Min profil</a>
</li>
{% endif %}
```

**Files to Modify:**
- Modify: `main/views.py` (add ProfileView)
- Modify: `main/urls.py` (add profile path)
- Create: `main/templates/main/profile.html`
- Modify: `main/templates/main/base.html` (add nav link)

---

### 2.2 Calendar - Click Booking for Details (P2)

**Goal**: Show booking details in a modal when clicking on calendar events.

#### Implementation Details

**Modify API Response (`main/views.py:261-283`):**

Enhance `BookingAPIView` to include more details:

```python
class BookingAPIView(LoginRequiredMixin, View):
    """API endpoint for calendar data (JSON)."""

    def get(self, request):
        bookings = Booking.objects.filter(
            status__in=['pending', 'confirmed'],
        ).select_related('user')

        events = []
        for booking in bookings:
            events.append({
                'id': booking.pk,
                'title': booking.user.username,
                'start': booking.start_date.isoformat(),
                'end': booking.end_date.isoformat(),
                'color': '#28a745' if booking.status == 'confirmed' else '#ffc107',
                'extendedProps': {
                    'status': booking.status,
                    'status_display': booking.get_status_display(),
                    'is_owner': booking.user == request.user,
                    'notes': booking.notes or '',
                    'duration': booking.duration_days,
                    'created_at': booking.created_at.strftime('%d. %B %Y'),
                    'user_email': booking.user.email if booking.user == request.user else '',
                    'edit_url': reverse('main:booking_update', args=[booking.pk]) if booking.user == request.user and booking.status == 'pending' else '',
                    'delete_url': reverse('main:booking_delete', args=[booking.pk]) if booking.user == request.user else '',
                },
            })

        return JsonResponse(events, safe=False)
```

**Calendar Template Update (`main/templates/main/kalender.html`):**

Add modal HTML and event click handler:

```html
<!-- Add after calendar legend, before calendar container -->

<!-- Booking Details Modal -->
<div class="modal fade" id="bookingModal" tabindex="-1" aria-labelledby="bookingModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="bookingModalLabel">Booking detaljer</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Luk"></button>
            </div>
            <div class="modal-body">
                <p><strong>Booket af:</strong> <span id="modal-user"></span></p>
                <p><strong>Periode:</strong> <span id="modal-dates"></span></p>
                <p><strong>Antal dage:</strong> <span id="modal-duration"></span></p>
                <p><strong>Status:</strong> <span id="modal-status"></span></p>
                <p id="modal-notes-container"><strong>Noter:</strong> <span id="modal-notes"></span></p>
                <p><strong>Oprettet:</strong> <span id="modal-created"></span></p>
            </div>
            <div class="modal-footer" id="modal-actions">
                <!-- Dynamic buttons inserted here -->
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Luk</button>
            </div>
        </div>
    </div>
</div>
```

**JavaScript Update (in same file):**

Add to FullCalendar initialization:

```javascript
var calendar = new FullCalendar.Calendar(calendarEl, {
    // ... existing config ...

    eventClick: function(info) {
        var event = info.event;
        var props = event.extendedProps;

        // Populate modal
        document.getElementById('modal-user').textContent = event.title;
        document.getElementById('modal-dates').textContent =
            formatDate(event.start) + ' - ' + formatDate(event.end);
        document.getElementById('modal-duration').textContent = props.duration + ' dage';
        document.getElementById('modal-status').innerHTML =
            '<span class="badge ' + (props.status === 'confirmed' ? 'bg-success' : 'bg-warning text-dark') + '">' +
            props.status_display + '</span>';
        document.getElementById('modal-created').textContent = props.created_at;

        // Notes (hide if empty)
        var notesContainer = document.getElementById('modal-notes-container');
        if (props.notes) {
            document.getElementById('modal-notes').textContent = props.notes;
            notesContainer.style.display = 'block';
        } else {
            notesContainer.style.display = 'none';
        }

        // Action buttons for owner
        var actionsDiv = document.getElementById('modal-actions');
        actionsDiv.innerHTML = '';  // Clear existing

        if (props.is_owner) {
            if (props.edit_url) {
                actionsDiv.innerHTML += '<a href="' + props.edit_url + '" class="btn btn-primary">Rediger</a>';
            }
            if (props.delete_url) {
                actionsDiv.innerHTML += '<a href="' + props.delete_url + '" class="btn btn-danger">Annuller</a>';
            }
        }
        actionsDiv.innerHTML += '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Luk</button>';

        // Show modal
        var modal = new bootstrap.Modal(document.getElementById('bookingModal'));
        modal.show();
    }
});

// Helper function for date formatting
function formatDate(date) {
    var options = { day: 'numeric', month: 'short', year: 'numeric' };
    return date.toLocaleDateString('da-DK', options);
}
```

**Files to Modify:**
- Modify: `main/views.py` (enhance BookingAPIView)
- Modify: `main/templates/main/kalender.html` (add modal and JS)

---

### 2.3 Calendar Export (ICS) (P2)

**Goal**: Allow users to export bookings to ICS format for calendar apps.

#### Implementation Details

**New View (`main/views.py`):**

```python
from django.http import HttpResponse


class BookingICSView(LoginRequiredMixin, View):
    """Generate ICS file for bookings."""

    def get(self, request, pk=None):
        if pk:
            # Single booking export
            booking = get_object_or_404(Booking, pk=pk)
            bookings = [booking]
            filename = f'vraa-booking-{pk}.ics'
        else:
            # All confirmed bookings
            bookings = Booking.objects.filter(status='confirmed')
            filename = 'vraa-bookinger.ics'

        # Generate ICS content
        ics_content = self._generate_ics(bookings)

        response = HttpResponse(ics_content, content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _generate_ics(self, bookings):
        """Generate ICS formatted calendar."""
        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Vraa//Booking System//DA',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
            'X-WR-CALNAME:Vraa Bookinger',
        ]

        for booking in bookings:
            uid = f'booking-{booking.pk}@vraa.org'
            dtstart = booking.start_date.strftime('%Y%m%d')
            dtend = booking.end_date.strftime('%Y%m%d')
            dtstamp = booking.created_at.strftime('%Y%m%dT%H%M%SZ')
            summary = f'Vraa: {booking.user.username}'
            description = booking.notes.replace('\n', '\\n') if booking.notes else ''

            lines.extend([
                'BEGIN:VEVENT',
                f'UID:{uid}',
                f'DTSTART;VALUE=DATE:{dtstart}',
                f'DTEND;VALUE=DATE:{dtend}',
                f'DTSTAMP:{dtstamp}',
                f'SUMMARY:{summary}',
            ])

            if description:
                lines.append(f'DESCRIPTION:{description}')

            lines.append('END:VEVENT')

        lines.append('END:VCALENDAR')
        return '\r\n'.join(lines)


class BookingICSFeedView(LoginRequiredMixin, View):
    """
    ICS feed URL for calendar subscription.
    Returns all confirmed bookings with a unique token per user.
    """

    def get(self, request):
        # All confirmed bookings
        bookings = Booking.objects.filter(
            status='confirmed'
        ).select_related('user')

        # Generate ICS
        view = BookingICSView()
        ics_content = view._generate_ics(bookings)

        response = HttpResponse(ics_content, content_type='text/calendar')
        response['Content-Disposition'] = 'inline; filename="vraa-calendar.ics"'
        return response
```

**URL Patterns (`main/urls.py`):**

```python
# ICS export
path('kalender/export/', views.BookingICSFeedView.as_view(), name='calendar_ics_feed'),
path('booking/<int:pk>/ics/', views.BookingICSView.as_view(), name='booking_ics'),
```

**Calendar Template Update (`main/templates/main/kalender.html`):**

Add export button near the "Book nu" button:

```html
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Kalender</h1>
    <div class="btn-group">
        <a href="{% url 'main:calendar_ics_feed' %}" class="btn btn-outline-secondary">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-calendar-plus me-1" viewBox="0 0 16 16">
                <path d="M8 7a.5.5 0 0 1 .5.5V9H10a.5.5 0 0 1 0 1H8.5v1.5a.5.5 0 0 1-1 0V10H6a.5.5 0 0 1 0-1h1.5V7.5A.5.5 0 0 1 8 7z"/>
                <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/>
            </svg>
            Eksporter til kalender
        </a>
        <a href="{% url 'main:booking_create' %}" class="btn btn-primary">
            Book nu
        </a>
    </div>
</div>
```

**Files to Modify:**
- Modify: `main/views.py` (add ICS views)
- Modify: `main/urls.py` (add ICS paths)
- Modify: `main/templates/main/kalender.html` (add export button)

---

## Phase 3: Communication Features

### 3.1 In-App Notification System (P2)

**Goal**: Alert users to comments, booking updates, and other events.

#### Database Schema

**New Model (`main/models.py`):**

```python
class Notification(models.Model):
    """User notification for various events."""

    NOTIFICATION_TYPES = [
        ('comment', 'Ny kommentar'),
        ('booking_approved', 'Booking godkendt'),
        ('booking_rejected', 'Booking afvist'),
        ('mention', 'Du blev nævnt'),
        ('reply', 'Svar på din kommentar'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Bruger',
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Type',
    )
    title = models.CharField(
        max_length=100,
        verbose_name='Titel',
    )
    message = models.TextField(
        max_length=500,
        verbose_name='Besked',
    )
    link = models.URLField(
        blank=True,
        verbose_name='Link',
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Læst',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oprettet',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notifikation'
        verbose_name_plural = 'Notifikationer'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self) -> str:
        return f'{self.user.username}: {self.title}'
```

**Notification Service (`main/services.py` - new file):**

```python
"""
Services for sending notifications and emails.
"""
from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .models import Notification


class NotificationService:
    """Service for creating and sending notifications."""

    @staticmethod
    def notify_comment_on_message(message, comment):
        """Notify message author when someone comments."""
        if message.author == comment.author:
            return  # Don't notify self

        Notification.objects.create(
            user=message.author,
            notification_type='comment',
            title='Ny kommentar på din besked',
            message=f'{comment.author.username} kommenterede: "{comment.content[:100]}..."',
            link=reverse('main:frontpage') + f'#message-{message.pk}',
        )

    @staticmethod
    def notify_booking_approved(booking):
        """Notify user when booking is approved."""
        Notification.objects.create(
            user=booking.user,
            notification_type='booking_approved',
            title='Din booking er godkendt!',
            message=f'Din booking fra {booking.start_date} til {booking.end_date} er blevet godkendt.',
            link=reverse('main:kalender'),
        )

    @staticmethod
    def notify_booking_rejected(booking):
        """Notify user when booking is rejected."""
        Notification.objects.create(
            user=booking.user,
            notification_type='booking_rejected',
            title='Din booking er afvist',
            message=f'Din booking fra {booking.start_date} til {booking.end_date} er desværre blevet afvist.',
            link=reverse('main:kalender'),
        )
```

**Views for Notifications (`main/views.py`):**

```python
class NotificationListView(LoginRequiredMixin, ListView):
    """Display user's notifications."""

    model = Notification
    template_name = 'main/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    extra_context = {'title': 'Notifikationer'}

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(LoginRequiredMixin, View):
    """Mark notification as read (AJAX)."""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, user=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """Mark all notifications as read."""

    def post(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return redirect('main:notifications')
```

**Context Processor for Unread Count (`main/context_processors.py` - new file):**

```python
"""
Context processors for the main app.
"""
from __future__ import annotations


def notifications(request):
    """Add unread notification count to context."""
    if request.user.is_authenticated:
        from .models import Notification
        unread_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return {'unread_notification_count': unread_count}
    return {'unread_notification_count': 0}
```

**Settings Update (`Vraa/settings.py:63-68`):**

Add context processor:

```python
'OPTIONS': {
    'context_processors': [
        # ... existing ...
        'main.context_processors.notifications',
    ],
},
```

**Base Template Update (`main/templates/main/base.html`):**

Add notification bell to sidebar:

```html
<!-- After user status section, before closing sidebar-sticky -->
{% if user.is_authenticated %}
<div class="notification-bell mt-3">
    <a href="{% url 'main:notifications' %}" class="btn btn-link position-relative">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8 16a2 2 0 0 0 2-2H6a2 2 0 0 0 2 2zM8 1.918l-.797.161A4.002 4.002 0 0 0 4 6c0 .628-.134 2.197-.459 3.742-.16.767-.376 1.566-.663 2.258h10.244c-.287-.692-.502-1.49-.663-2.258C12.134 8.197 12 6.628 12 6a4.002 4.002 0 0 0-3.203-3.92L8 1.917zM14.22 12c.223.447.481.801.78 1H1c.299-.199.557-.553.78-1C2.68 10.2 3 6.88 3 6c0-2.42 1.72-4.44 4.005-4.901a1 1 0 1 1 1.99 0A5.002 5.002 0 0 1 13 6c0 .88.32 4.2 1.22 6z"/>
        </svg>
        {% if unread_notification_count > 0 %}
        <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
            {{ unread_notification_count }}
            <span class="visually-hidden">ulæste notifikationer</span>
        </span>
        {% endif %}
    </a>
</div>
{% endif %}
```

**Files to Create/Modify:**
- Modify: `main/models.py` (add Notification model)
- Create: `main/services.py`
- Create: `main/context_processors.py`
- Modify: `main/views.py` (add notification views)
- Modify: `main/urls.py` (add notification URLs)
- Create: `main/templates/main/notifications.html`
- Modify: `main/templates/main/base.html` (add bell icon)
- Modify: `Vraa/settings.py` (add context processor)
- Run: `python manage.py makemigrations && python manage.py migrate`

---

### 3.2 Pin Important Messages (P2)

**Goal**: Allow admins to pin messages to the top of the message board.

#### Implementation Details

**Model Update (`main/models.py:10-45`):**

Add field to Message model:

```python
class Message(models.Model):
    """A message on the message board."""

    author = models.ForeignKey(...)
    content = models.TextField(...)
    created_at = models.DateTimeField(...)
    updated_at = models.DateTimeField(...)
    is_pinned = models.BooleanField(
        default=False,
        verbose_name='Fastgjort',
        help_text='Fastgjorte beskeder vises øverst på opslagstavlen',
    )
    pinned_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fastgjort tidspunkt',
    )
    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pinned_messages',
        verbose_name='Fastgjort af',
    )

    class Meta:
        ordering = ['-is_pinned', '-pinned_at', '-created_at']  # Pinned first
        # ... rest unchanged
```

**View Update (`main/views.py:27-41`):**

```python
class FrontpageView(ListView):
    """Display the frontpage with the message board."""

    model = Message
    template_name = 'main/frontpage.html'
    context_object_name = 'message_list'
    paginate_by = 20
    extra_context = {'title': 'Forside'}

    def get_queryset(self):
        return Message.objects.select_related('author').prefetch_related(
            'comments',
            'comments__author',
        ).order_by('-is_pinned', '-pinned_at', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Separate pinned and regular messages for template
        all_messages = list(context['message_list'])
        context['pinned_messages'] = [m for m in all_messages if m.is_pinned]
        context['regular_messages'] = [m for m in all_messages if not m.is_pinned]
        return context
```

**Admin Action (`main/admin.py`):**

```python
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_preview', 'is_pinned', 'created_at']
    list_filter = ['is_pinned', 'created_at']
    search_fields = ['content', 'author__username']
    actions = ['pin_messages', 'unpin_messages']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Indhold'

    @admin.action(description='Fastgør valgte beskeder')
    def pin_messages(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_pinned=True, pinned_at=timezone.now(), pinned_by=request.user)
        self.message_user(request, f'{queryset.count()} besked(er) fastgjort.')

    @admin.action(description='Fjern fastgørelse fra valgte beskeder')
    def unpin_messages(self, request, queryset):
        queryset.update(is_pinned=False, pinned_at=None, pinned_by=None)
        self.message_user(request, f'{queryset.count()} besked(er) ikke længere fastgjort.')
```

**Template Update (`main/templates/main/frontpage.html`):**

Add pinned messages section:

```html
{% if pinned_messages %}
<div class="pinned-messages mb-4">
    <h5 class="text-muted">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pin-fill me-1" viewBox="0 0 16 16">
            <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A5.921 5.921 0 0 1 5 6.708V2.277a2.77 2.77 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354z"/>
        </svg>
        Fastgjorte beskeder
    </h5>
    {% for message in pinned_messages %}
    <div class="card mb-3 border-primary pinned-message" id="message-{{ message.pk }}">
        <!-- Message content same as regular, with pin indicator -->
    </div>
    {% endfor %}
</div>
{% endif %}

<h5 class="text-muted mb-3">Alle beskeder</h5>
{% for message in regular_messages %}
<!-- Regular message cards -->
{% endfor %}
```

**CSS Addition (`main/static/main/css/style.css`):**

```css
.pinned-message {
    border-left: 4px solid var(--primary-blue) !important;
    background-color: var(--accent-sand-light, #faf6f0);
}

.pinned-messages .card-header {
    background-color: rgba(44, 95, 124, 0.1);
}
```

**Files to Modify:**
- Modify: `main/models.py` (add is_pinned fields)
- Modify: `main/views.py` (update FrontpageView)
- Modify: `main/admin.py` (add pin/unpin actions)
- Modify: `main/templates/main/frontpage.html` (pinned section)
- Modify: `main/static/main/css/style.css` (pinned styling)
- Run: `python manage.py makemigrations && python manage.py migrate`

---

### 3.3 Message Reactions (P3)

**Goal**: Allow users to react to messages with emojis.

#### Database Schema

**New Model (`main/models.py`):**

```python
class Reaction(models.Model):
    """An emoji reaction on a message."""

    REACTION_CHOICES = [
        ('thumbsup', '👍'),
        ('heart', '❤️'),
        ('laugh', '😄'),
        ('celebrate', '🎉'),
        ('thinking', '🤔'),
    ]

    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='Besked',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='Bruger',
    )
    reaction_type = models.CharField(
        max_length=20,
        choices=REACTION_CHOICES,
        verbose_name='Reaktion',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oprettet',
    )

    class Meta:
        verbose_name = 'Reaktion'
        verbose_name_plural = 'Reaktioner'
        unique_together = ['message', 'user', 'reaction_type']  # One reaction type per user per message
        indexes = [
            models.Index(fields=['message']),
        ]

    def __str__(self) -> str:
        return f'{self.user.username} reacted {self.get_reaction_type_display()} to {self.message.pk}'
```

**AJAX View (`main/views.py`):**

```python
class ReactionToggleView(LoginRequiredMixin, View):
    """Toggle a reaction on a message (AJAX)."""

    def post(self, request, message_pk, reaction_type):
        from .models import Reaction, Message

        message = get_object_or_404(Message, pk=message_pk)

        # Check if reaction exists
        existing = Reaction.objects.filter(
            message=message,
            user=request.user,
            reaction_type=reaction_type,
        ).first()

        if existing:
            existing.delete()
            action = 'removed'
        else:
            Reaction.objects.create(
                message=message,
                user=request.user,
                reaction_type=reaction_type,
            )
            action = 'added'

        # Get updated counts
        counts = {}
        for rt, _ in Reaction.REACTION_CHOICES:
            counts[rt] = Reaction.objects.filter(
                message=message, reaction_type=rt
            ).count()

        return JsonResponse({
            'action': action,
            'counts': counts,
        })
```

---

### 3.4 Photo Sharing (P3)

**Goal**: Allow users to attach images to messages.

#### Implementation Details

**Model Update (`main/models.py`):**

Add image field to Message:

```python
import os
from django.core.validators import FileExtensionValidator


def message_image_path(instance, filename):
    """Generate upload path for message images."""
    ext = filename.split('.')[-1]
    return f'messages/{instance.author.pk}/{instance.pk or "new"}.{ext}'


class Message(models.Model):
    # ... existing fields ...

    image = models.ImageField(
        upload_to=message_image_path,
        blank=True,
        null=True,
        verbose_name='Billede',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
    )
```

**Settings for Media Files (`Vraa/settings.py`):**

```python
# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# For production with S3/Cloudinary (example):
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
```

**URL Update (`Vraa/urls.py`):**

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... existing patterns ...
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Form Update (`main/forms.py`):**

```python
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }
```

**Dependencies:**

Add to `pyproject.toml`:
```toml
Pillow = "^10.0.0"
```

---

## Phase 4: Administrative Tools

### 4.1 Document Management System (P2)

**Goal**: Allow admins to upload and manage referater/vedtaegter via admin.

#### Database Schema

**New Model (`main/models.py`):**

```python
import os


def document_upload_path(instance, filename):
    """Generate upload path based on category and year."""
    ext = filename.split('.')[-1]
    year = instance.document_date.year if instance.document_date else 'other'
    return f'documents/{instance.category}/{year}/{filename}'


class Document(models.Model):
    """A document (referat, vedtaegt, etc.)"""

    CATEGORY_CHOICES = [
        ('referat', 'Referat'),
        ('vedtaegt', 'Vedtægt'),
        ('other', 'Andet'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name='Titel',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Kategori',
    )
    file = models.FileField(
        upload_to=document_upload_path,
        verbose_name='Fil',
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])],
    )
    document_date = models.DateField(
        verbose_name='Dokument dato',
        help_text='Datoen for dokumentet (f.eks. dato for generalforsamling)',
    )
    description = models.TextField(
        blank=True,
        max_length=500,
        verbose_name='Beskrivelse',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name='Uploadet af',
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Uploadet',
    )

    class Meta:
        ordering = ['-document_date']
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumenter'
        indexes = [
            models.Index(fields=['category', '-document_date']),
        ]

    def __str__(self) -> str:
        return f'{self.get_category_display()}: {self.title}'
```

**Admin Configuration (`main/admin.py`):**

```python
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'document_date', 'uploaded_by', 'uploaded_at']
    list_filter = ['category', 'document_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'document_date'
    readonly_fields = ['uploaded_by', 'uploaded_at']

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
```

**Dynamic View Update (`main/views.py`):**

```python
class ReferaterView(TemplateView):
    template_name = 'main/referater.html'
    extra_context = {'title': 'Referater'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get documents from database
        documents = Document.objects.filter(category='referat')

        # Group by year
        years = {}
        for doc in documents:
            year = doc.document_date.year
            if year not in years:
                years[year] = []
            years[year].append(doc)

        context['documents_by_year'] = dict(sorted(years.items(), reverse=True))
        return context
```

---

### 4.2 User Management Dashboard (P2)

**Goal**: Provide admin view for managing users without full Django admin.

#### Implementation Details

**New Views (`main/views.py`):**

```python
class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Dashboard for managing users (staff only)."""

    model = User
    template_name = 'main/user_management.html'
    context_object_name = 'users'
    extra_context = {'title': 'Brugerstyring'}

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_users'] = User.objects.filter(is_active=False)
        context['active_users'] = User.objects.filter(is_active=True)
        return context


class UserActivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Activate a pending user (staff only)."""

    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.save()

        # Send welcome email
        if user.email:
            send_mail(
                subject='Din konto er aktiveret - Vraa',
                message=(
                    f'Hej {user.username},\n\n'
                    f'Din konto på Vraa-hjemmesiden er nu aktiveret.\n'
                    f'Du kan nu logge ind og bruge siden.\n\n'
                    f'Venlig hilsen,\nVraa'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        messages.success(request, f'Brugeren {user.username} er nu aktiveret.')
        return redirect('main:user_management')


class UserDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Deactivate a user (staff only)."""

    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'Du kan ikke deaktivere din egen konto.')
        else:
            user.is_active = False
            user.save()
            messages.success(request, f'Brugeren {user.username} er nu deaktiveret.')
        return redirect('main:user_management')
```

**URL Patterns:**

```python
# Admin management
path('admin-dashboard/brugere/', views.UserManagementView.as_view(), name='user_management'),
path('admin-dashboard/brugere/<int:pk>/aktiver/', views.UserActivateView.as_view(), name='user_activate'),
path('admin-dashboard/brugere/<int:pk>/deaktiver/', views.UserDeactivateView.as_view(), name='user_deactivate'),
```

---

### 4.3 Audit/Activity Log (P3)

**Goal**: Track important actions for accountability.

#### Database Schema

**New Model (`main/models.py`):**

```python
class AuditLog(models.Model):
    """Log of important actions for accountability."""

    ACTION_CHOICES = [
        ('booking_approved', 'Booking godkendt'),
        ('booking_rejected', 'Booking afvist'),
        ('user_activated', 'Bruger aktiveret'),
        ('user_deactivated', 'Bruger deaktiveret'),
        ('message_deleted', 'Besked slettet'),
        ('document_uploaded', 'Dokument uploadet'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='Bruger',
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='Handling',
    )
    target_type = models.CharField(
        max_length=50,
        verbose_name='Måltype',
        help_text='Model name of the affected object',
    )
    target_id = models.PositiveIntegerField(
        verbose_name='Mål-ID',
        help_text='Primary key of the affected object',
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Detaljer',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP-adresse',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Tidspunkt',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Aktivitetslog'
        verbose_name_plural = 'Aktivitetslogs'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]

    def __str__(self) -> str:
        return f'{self.user}: {self.get_action_display()} ({self.created_at})'
```

**Logging Service (`main/services.py`):**

```python
class AuditService:
    """Service for logging audit events."""

    @staticmethod
    def log(request, action, target, details=None):
        """Create an audit log entry."""
        from .models import AuditLog

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            target_type=target.__class__.__name__,
            target_id=target.pk,
            details=details or {},
            ip_address=ip,
        )
```

---

## Phase 5: Quality of Life Features

### 5.1 Dark Mode (P3)

**Goal**: Support dark color scheme preference.

#### Implementation Details

**CSS Variables for Dark Mode (`main/static/main/css/style.css`):**

```css
/* Dark mode color scheme */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #1a1a2e;
        --bg-secondary: #16213e;
        --bg-accent: #0f3460;
        --text-primary: #eaeaea;
        --text-secondary: #b4b4b4;
        --border-color: #2a2a4a;
        --card-bg: #1f1f3a;
        --shadow-color: rgba(0, 0, 0, 0.5);
    }
}

/* Manual dark mode toggle class */
[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-accent: #0f3460;
    --text-primary: #eaeaea;
    --text-secondary: #b4b4b4;
    --border-color: #2a2a4a;
    --card-bg: #1f1f3a;
    --shadow-color: rgba(0, 0, 0, 0.5);
}

/* Smooth transition between themes */
body {
    transition: background-color 0.3s ease, color 0.3s ease;
}
```

**JavaScript for Theme Toggle (`main/static/main/js/theme.js` - new file):**

```javascript
// Theme Toggle
(function() {
    const THEME_KEY = 'vraa-theme';

    // Get saved theme or system preference
    function getPreferredTheme() {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved) return saved;

        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light';
    }

    // Apply theme
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);

        // Update toggle button icon
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
            btn.setAttribute('aria-label',
                theme === 'dark' ? 'Skift til lyst tema' : 'Skift til mørkt tema'
            );
        }
    }

    // Toggle theme
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        setTheme(current === 'dark' ? 'light' : 'dark');
    }

    // Initialize on load
    document.addEventListener('DOMContentLoaded', function() {
        setTheme(getPreferredTheme());

        // Add toggle button listener
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.addEventListener('click', toggleTheme);
        }
    });

    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)')
        .addEventListener('change', e => {
            if (!localStorage.getItem(THEME_KEY)) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        });
})();
```

**Base Template Update:**

Add toggle button and script:

```html
<!-- In sidebar, after user status -->
<button id="theme-toggle" class="btn btn-link" aria-label="Skift tema">
    🌙
</button>

<!-- Before closing body tag -->
<script src="{% static 'main/js/theme.js' %}"></script>
```

---

### 5.2 Weather Widget (P3)

**Goal**: Show weather at Vraa location.

#### Implementation Details

**Weather Service (`main/services.py`):**

```python
import requests
from django.core.cache import cache


class WeatherService:
    """Service for fetching weather data from yr.no."""

    # Vraa coordinates (example - replace with actual)
    LAT = 57.0000
    LON = 9.9000
    CACHE_KEY = 'vraa_weather'
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_weather(cls):
        """Fetch current weather, with caching."""
        cached = cache.get(cls.CACHE_KEY)
        if cached:
            return cached

        try:
            url = f'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={cls.LAT}&lon={cls.LON}'
            headers = {'User-Agent': 'VraaWebsite/1.0 (contact@vraa.org)'}

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            timeseries = data['properties']['timeseries']

            # Current weather (first entry)
            current = timeseries[0]['data']['instant']['details']
            weather = {
                'temperature': round(current['air_temperature']),
                'wind_speed': round(current['wind_speed']),
                'humidity': round(current.get('relative_humidity', 0)),
                'updated': timeseries[0]['time'],
            }

            # Forecast (next 3 days)
            weather['forecast'] = []
            for i in range(0, min(72, len(timeseries)), 24):
                entry = timeseries[i]
                weather['forecast'].append({
                    'time': entry['time'],
                    'temp': round(entry['data']['instant']['details']['air_temperature']),
                })

            cache.set(cls.CACHE_KEY, weather, cls.CACHE_TIMEOUT)
            return weather

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Weather fetch failed: {e}')
            return None
```

**Context Processor or Template Tag:**

Add to context for information page.

---

### 5.3 Maintenance Request System (P3)

**Goal**: Allow users to report issues at the property.

#### Database Schema

**New Model (`main/models.py`):**

```python
class MaintenanceRequest(models.Model):
    """A maintenance request for the vacation home."""

    STATUS_CHOICES = [
        ('pending', 'Afventer'),
        ('in_progress', 'Under behandling'),
        ('resolved', 'Løst'),
        ('wont_fix', 'Afvist'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Lav'),
        ('medium', 'Normal'),
        ('high', 'Høj'),
        ('urgent', 'Akut'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        verbose_name='Indberetter',
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Titel',
    )
    description = models.TextField(
        max_length=2000,
        verbose_name='Beskrivelse',
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Placering',
        help_text='Hvor på ejendommen er problemet?',
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Prioritet',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status',
    )
    admin_notes = models.TextField(
        blank=True,
        max_length=1000,
        verbose_name='Admin noter',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oprettet',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Opdateret',
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Løst',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vedligeholdelsesanmodning'
        verbose_name_plural = 'Vedligeholdelsesanmodninger'

    def __str__(self) -> str:
        return f'{self.title} ({self.get_status_display()})'
```

---

## Phase 6: Technical Improvements

### 6.1 HTMX Integration (P2)

**Goal**: Add dynamic interactions without full page reloads.

#### Implementation Details

**Add HTMX to Base Template (`main/templates/main/base.html`):**

```html
<!-- Before closing body tag -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script src="https://unpkg.com/htmx.org@1.9.10/dist/ext/json-enc.js"></script>
```

**HTMX-enabled Comment Form:**

```html
<!-- In frontpage.html -->
<form hx-post="{% url 'main:comment_create' message.pk %}"
      hx-target="#comments-{{ message.pk }}"
      hx-swap="beforeend"
      hx-on::after-request="this.reset()">
    {% csrf_token %}
    <div class="input-group">
        <input type="text" name="content" class="form-control"
               placeholder="Skriv en kommentar..." required>
        <button type="submit" class="btn btn-outline-primary">Send</button>
    </div>
</form>
```

**HTMX-aware View (`main/views.py`):**

```python
class CommentCreateView(LoginRequiredMixin, CreateView):
    """Create a new comment, with HTMX support."""

    model = Comment
    fields = ['content']
    template_name = 'main/comment_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.message_id = self.kwargs['message_pk']
        self.object = form.save()

        # If HTMX request, return partial
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'main/partials/comment.html', {
                'comment': self.object
            })

        return redirect('main:frontpage')
```

**Partial Template (`main/templates/main/partials/comment.html`):**

```html
<div class="comment mb-2" id="comment-{{ comment.pk }}">
    <small class="text-muted">
        {{ comment.author.username }} · {{ comment.created_at|timesince }} siden
    </small>
    <p class="mb-1">{{ comment.content }}</p>
</div>
```

---

### 6.2 Progressive Web App (PWA) (P3)

**Goal**: Enable installation and offline access.

#### Implementation Details

**Web App Manifest (`main/static/main/manifest.json`):**

```json
{
    "name": "Vraa Feriehus",
    "short_name": "Vraa",
    "description": "Vraa feriehus - booking og information",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#F4E9D8",
    "theme_color": "#2C5F7C",
    "icons": [
        {
            "src": "/static/main/img/logo-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/static/main/img/logo-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

**Service Worker (`main/static/main/sw.js`):**

```javascript
const CACHE_NAME = 'vraa-v1';
const STATIC_ASSETS = [
    '/',
    '/static/main/css/style.css',
    '/static/main/img/logo.png',
];

// Install
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
    );
});

// Fetch with network-first strategy
self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request)
            .catch(() => caches.match(event.request))
    );
});
```

**Base Template Updates:**

```html
<head>
    <link rel="manifest" href="{% static 'main/manifest.json' %}">
    <meta name="theme-color" content="#2C5F7C">
    <meta name="apple-mobile-web-app-capable" content="yes">
</head>

<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/main/sw.js');
}
</script>
```

---

### 6.3 API Rate Limiting (P3)

**Goal**: Protect API endpoints from abuse.

#### Implementation Details

**Install django-ratelimit:**

```toml
# pyproject.toml
django-ratelimit = "^4.0.0"
```

**Apply to Booking API (`main/views.py`):**

```python
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator


@method_decorator(ratelimit(key='user', rate='60/h', method='GET'), name='get')
class BookingAPIView(LoginRequiredMixin, View):
    """API endpoint for calendar data (JSON) with rate limiting."""
    # ... existing code ...
```

---

## Database Schema Changes

### Summary of New Models

| Model | Phase | Migration Required |
|-------|-------|-------------------|
| `Notification` | 3.1 | Yes |
| `Reaction` | 3.3 | Yes |
| `Document` | 4.1 | Yes |
| `AuditLog` | 4.3 | Yes |
| `MaintenanceRequest` | 5.3 | Yes |

### Model Modifications

| Model | Field | Phase | Migration Required |
|-------|-------|-------|-------------------|
| `Message` | `is_pinned`, `pinned_at`, `pinned_by` | 3.2 | Yes |
| `Message` | `image` | 3.4 | Yes |

### Migration Strategy

1. Create migrations incrementally per feature
2. Test migrations locally before deploying
3. Back up production database before applying
4. Use `--fake` if needed for data-only migrations

```bash
# Per feature branch
python manage.py makemigrations main
python manage.py migrate

# Production deployment
heroku run python manage.py migrate
```

---

## Testing Strategy

### Unit Tests

For each feature, create tests in `main/tests.py`:

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Message, Booking, Notification


class LoginRequiredMiddlewareTest(TestCase):
    """Test site-wide login requirement."""

    def test_anonymous_redirect(self):
        """Anonymous users redirected to login."""
        response = self.client.get('/')
        self.assertRedirects(response, '/login/?next=/')

    def test_login_page_accessible(self):
        """Login page accessible without auth."""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_authenticated_access(self):
        """Authenticated users can access pages."""
        user = User.objects.create_user('test', 'test@test.com', 'password')
        self.client.login(username='test', password='password')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class NotificationTest(TestCase):
    """Test notification system."""

    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'password')

    def test_notification_created(self):
        """Notifications created correctly."""
        Notification.objects.create(
            user=self.user,
            notification_type='comment',
            title='Test',
            message='Test message',
        )
        self.assertEqual(self.user.notifications.count(), 1)

    def test_unread_count(self):
        """Unread count accurate."""
        Notification.objects.create(user=self.user, notification_type='comment', title='1', message='1')
        Notification.objects.create(user=self.user, notification_type='comment', title='2', message='2', is_read=True)
        self.assertEqual(self.user.notifications.filter(is_read=False).count(), 1)
```

### Integration Tests

Test complete workflows:

```python
class BookingWorkflowTest(TestCase):
    """Test complete booking workflow with notifications."""

    def test_booking_approval_flow(self):
        """Test booking creation through approval with notification."""
        # Create user and booking
        user = User.objects.create_user('guest', 'guest@test.com', 'password')
        admin = User.objects.create_superuser('admin', 'admin@test.com', 'password')

        self.client.login(username='guest', password='password')

        # Create booking
        response = self.client.post(reverse('main:booking_create'), {
            'start_date': '2026-03-01',
            'end_date': '2026-03-05',
            'notes': 'Test booking',
        })

        booking = Booking.objects.first()
        self.assertEqual(booking.status, 'pending')

        # Admin approves
        self.client.login(username='admin', password='password')
        booking.status = 'confirmed'
        booking.save()

        # Check notification created (if notification service is integrated)
```

### Running Tests

```bash
# Run all tests
uv run python manage.py test

# Run specific test module
uv run python manage.py test main.tests.NotificationTest

# Run with coverage
uv run coverage run manage.py test
uv run coverage report
```

---

## Deployment Considerations

### Pre-Deployment Checklist

For each feature deployment:

1. **Database**
   - [ ] Migrations created and tested locally
   - [ ] Production database backed up
   - [ ] Migration plan reviewed (backwards compatible?)

2. **Static Files**
   - [ ] `collectstatic` run
   - [ ] New JS/CSS files minified (optional)
   - [ ] CDN cache cleared if necessary

3. **Environment Variables**
   - [ ] New env vars documented
   - [ ] Heroku config vars set
   - [ ] Secrets rotated if needed

4. **Testing**
   - [ ] Unit tests passing
   - [ ] Integration tests passing
   - [ ] Manual QA completed

5. **Monitoring**
   - [ ] Error tracking configured (Sentry?)
   - [ ] Performance monitoring set up

### Rollback Plan

For each deployment:

```bash
# If issues occur, rollback migration
heroku run python manage.py migrate main <previous_migration_number>

# Rollback code
git revert <commit_hash>
git push heroku main
```

### Performance Considerations

1. **Database Indexes**: All new models include appropriate indexes
2. **Query Optimization**: Use `select_related` and `prefetch_related`
3. **Caching**: Cache expensive operations (weather, notifications count)
4. **Static Files**: WhiteNoise with compression enabled

### Security Considerations

1. **CSRF Protection**: All forms use `{% csrf_token %}`
2. **XSS Prevention**: Django templates auto-escape
3. **Permission Checks**: `UserPassesTestMixin` for staff-only views
4. **Rate Limiting**: Applied to API endpoints
5. **Input Validation**: Form validation on all user input

---

## Implementation Order Recommendation

Based on dependencies and impact:

### Sprint 1 (Highest Priority)
1. Login Required Middleware (1.1)
2. Password Reset (1.2)
3. Booking Email Notifications (1.3)

### Sprint 2 (Core User Experience)
4. User Profile Page (2.1)
5. Calendar Click Details (2.2)
6. ICS Export (2.3)

### Sprint 3 (Communication)
7. Pin Messages (3.2)
8. Notification System (3.1)

### Sprint 4 (Administration)
9. Document Management (4.1)
10. User Management Dashboard (4.2)

### Sprint 5 (Enhancements)
11. HTMX Integration (6.1)
12. Reactions (3.3)
13. Dark Mode (5.1)

### Sprint 6 (Nice to Have)
14. Photo Sharing (3.4)
15. Maintenance Requests (5.3)
16. Weather Widget (5.2)
17. Audit Log (4.3)
18. PWA (6.2)
19. Rate Limiting (6.3)

---

## Appendix: File Change Summary

### New Files to Create

| File | Purpose |
|------|---------|
| `main/middleware.py` | Login required middleware |
| `main/services.py` | Notification & weather services |
| `main/context_processors.py` | Template context processors |
| `main/templates/main/password_reset*.html` | Password reset templates (6 files) |
| `main/templates/main/profile.html` | User profile page |
| `main/templates/main/notifications.html` | Notifications list |
| `main/templates/main/user_management.html` | Admin user dashboard |
| `main/templates/main/partials/*.html` | HTMX partial templates |
| `main/static/main/js/theme.js` | Dark mode toggle |
| `main/static/main/manifest.json` | PWA manifest |
| `main/static/main/sw.js` | Service worker |

### Files to Modify

| File | Changes |
|------|---------|
| `Vraa/settings.py` | Middleware, context processors, media config |
| `main/models.py` | New models, field additions |
| `main/views.py` | New views, HTMX support |
| `main/urls.py` | New URL patterns |
| `main/admin.py` | Enhanced admin with actions |
| `main/templates/main/base.html` | Navigation, notification bell, theme toggle |
| `main/templates/main/kalender.html` | Modal, ICS button, event click |
| `main/templates/main/frontpage.html` | Pinned messages, reactions |
| `main/templates/main/login.html` | Forgot password link |
| `main/static/main/css/style.css` | Dark mode, pinned styles |
| `pyproject.toml` | New dependencies |

---

**Document Complete**

This implementation plan provides detailed technical specifications for all features in the Vraa roadmap. Each section includes code examples, file locations, and testing guidance to enable efficient implementation.
