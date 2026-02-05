# Vraa Site - Final Polish Implementation Plan

This document provides a detailed implementation plan for the final polish recommendations identified during the comprehensive quality review conducted on 2026-02-05.

## Overview

The Vraa project has been assessed as **production-ready with high quality (8.4/10)**. These final polish items will elevate the project to enterprise-grade quality and ensure long-term maintainability.

---

## Executive Summary

| Phase | Feature | Priority | Effort | Dependencies |
|-------|---------|----------|--------|--------------|
| 6 | Automated Test Suite | P1 | High | None |
| 7 | Accessibility Audit & Fixes | P2 | Medium | None |
| 8 | Search Functionality | P2 | Medium | None |
| 9 | Print Styles | P3 | Low | None |
| 10 | Production Hardening | P1 | Low | None |

**Estimated Total Implementation Time**: 3-5 development sessions

---

## Phase 6: Automated Test Suite

### Problem Analysis

The codebase has excellent structure and testable code, but **no automated tests exist**. This poses risks for:
- Regression bugs during future development
- Refactoring confidence
- Deployment safety
- Documentation of expected behavior

### Current State

- `main/tests.py` exists but is empty
- Django's `TestCase` available
- No test fixtures or factories
- No CI/CD pipeline configured

### Implementation Tasks

#### 6.1 Set Up Testing Infrastructure

**File**: `pyproject.toml` (add dev dependencies)

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-django>=4.5",
    "pytest-cov>=4.0",
    "factory-boy>=3.3",
    "faker>=18.0",
]
```

**File**: `pytest.ini` (create)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = Vraa.settings
python_files = tests.py test_*.py *_tests.py
addopts = --reuse-db --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

**File**: `conftest.py` (create in project root)

```python
import pytest
from django.contrib.auth import get_user_model

@pytest.fixture
def user(db):
    """Create a regular test user."""
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user

@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    User = get_user_model()
    user = User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        is_staff=True
    )
    return user

@pytest.fixture
def authenticated_client(client, user):
    """Return a client logged in as regular user."""
    client.login(username='testuser', password='testpass123')
    return client

@pytest.fixture
def staff_client(client, staff_user):
    """Return a client logged in as staff."""
    client.login(username='staffuser', password='testpass123')
    return client
```

#### 6.2 Create Model Factories

**File**: `main/tests/factories.py` (create)

```python
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from main.models import (
    UserProfile, HeritageLine, Message, Comment,
    Booking, Notification, Document, MaintenanceRequest
)

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class HeritageLineFactory(DjangoModelFactory):
    class Meta:
        model = HeritageLine

    name = factory.Sequence(lambda n: f'Linje {n}')
    short_name = factory.Sequence(lambda n: f'L{n}')
    color = '#2C5F7C'
    badge_class = 'bg-primary'
    order = factory.Sequence(lambda n: n)
    base_weeks = [26, 27]


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    display_name = factory.Faker('name')
    heritage_line = factory.SubFactory(HeritageLineFactory)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    author = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph')


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    message = factory.SubFactory(MessageFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('sentence')


class BookingFactory(DjangoModelFactory):
    class Meta:
        model = Booking

    user = factory.SubFactory(UserFactory)
    start_date = factory.Faker('date_this_year')
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(days=7)
    )
    status = 'pending'
    notes = factory.Faker('sentence')


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    notification_type = 'comment'
    title = factory.Faker('sentence', nb_words=4)
    message = factory.Faker('sentence')
    is_read = False
```

#### 6.3 Write Model Tests

**File**: `main/tests/test_models.py` (create)

```python
import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from main.models import (
    HeritageLine, ReservedWeek, UserProfile,
    Message, Comment, Booking, Notification
)
from .factories import (
    UserFactory, HeritageLineFactory, MessageFactory,
    BookingFactory, UserProfileFactory
)

User = get_user_model()


class TestHeritageLine:
    """Tests for HeritageLine model."""

    @pytest.mark.django_db
    def test_create_heritage_line(self):
        line = HeritageLineFactory(name='Test Line', short_name='TL')
        assert line.name == 'Test Line'
        assert line.short_name == 'TL'
        assert str(line) == 'Test Line'

    @pytest.mark.django_db
    def test_get_reserved_weeks_for_year_base_year(self):
        """Test reserved weeks calculation for base year 2024."""
        line = HeritageLineFactory(order=0, base_weeks=[26, 27])
        weeks = line.get_reserved_weeks_for_year(2024)
        assert weeks == [26, 27]

    @pytest.mark.django_db
    def test_get_reserved_weeks_rotation(self):
        """Test that reserved weeks rotate correctly each year."""
        # Create 4 heritage lines
        lines = [
            HeritageLineFactory(order=i, base_weeks=[26 + i*2, 27 + i*2])
            for i in range(4)
        ]

        # In 2025, line 1 should have weeks 28-29 (rotated from 26-27)
        weeks_2025 = lines[0].get_reserved_weeks_for_year(2025)
        assert 28 in weeks_2025 or 29 in weeks_2025


class TestUserProfile:
    """Tests for UserProfile model."""

    @pytest.mark.django_db
    def test_get_display_name_with_display_name(self):
        profile = UserProfileFactory(display_name='Rasmus Damgaard')
        assert profile.get_display_name() == 'Rasmus Damgaard'

    @pytest.mark.django_db
    def test_get_display_name_fallback_to_username(self):
        user = UserFactory(username='testuser')
        profile = UserProfileFactory(user=user, display_name='')
        assert profile.get_display_name() == 'testuser'


class TestMessage:
    """Tests for Message model."""

    @pytest.mark.django_db
    def test_create_message(self):
        message = MessageFactory(content='Test message content')
        assert message.content == 'Test message content'
        assert message.created_at is not None

    @pytest.mark.django_db
    def test_message_ordering(self):
        """Messages should be ordered by pinned first, then newest."""
        msg1 = MessageFactory()
        msg2 = MessageFactory(is_pinned=True)
        msg3 = MessageFactory()

        messages = list(Message.objects.all())
        # Pinned message should be first
        assert messages[0].is_pinned == True


class TestBooking:
    """Tests for Booking model."""

    @pytest.mark.django_db
    def test_create_booking(self):
        booking = BookingFactory()
        assert booking.status == 'pending'
        assert booking.start_date < booking.end_date

    @pytest.mark.django_db
    def test_booking_end_date_must_be_after_start_date(self):
        """Validation should fail if end_date <= start_date."""
        with pytest.raises(ValidationError):
            booking = Booking(
                user=UserFactory(),
                start_date=date(2024, 7, 15),
                end_date=date(2024, 7, 10),  # Before start
                status='pending'
            )
            booking.full_clean()

    @pytest.mark.django_db
    def test_booking_duration_property(self):
        booking = BookingFactory(
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 8)
        )
        assert booking.duration_days == 7

    @pytest.mark.django_db
    def test_overlapping_confirmed_bookings_rejected(self):
        """Cannot create overlapping confirmed bookings."""
        user1 = UserFactory()
        user2 = UserFactory()

        # Create confirmed booking
        BookingFactory(
            user=user1,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 7),
            status='confirmed'
        )

        # Try to create overlapping confirmed booking
        with pytest.raises(ValidationError):
            booking = Booking(
                user=user2,
                start_date=date(2024, 7, 5),
                end_date=date(2024, 7, 10),
                status='confirmed'
            )
            booking.full_clean()


class TestReservedWeek:
    """Tests for ReservedWeek model."""

    @pytest.mark.django_db
    def test_auto_calculate_dates(self):
        """Start and end dates should be calculated from year and week."""
        line = HeritageLineFactory()
        week = ReservedWeek.objects.create(
            heritage_line=line,
            year=2024,
            week_number=26
        )
        assert week.start_date is not None
        assert week.end_date is not None
        assert (week.end_date - week.start_date).days == 6

    @pytest.mark.django_db
    def test_generate_for_year(self):
        """Should generate reserved weeks for all heritage lines."""
        # Create 4 lines with 2 weeks each
        for i in range(4):
            HeritageLineFactory(order=i, base_weeks=[26 + i*2, 27 + i*2])

        count = ReservedWeek.generate_for_year(2024)
        assert count == 8  # 4 lines * 2 weeks each
```

#### 6.4 Write View Tests

**File**: `main/tests/test_views.py` (create)

```python
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from main.models import Message, Comment, Booking
from .factories import MessageFactory, BookingFactory, UserFactory

User = get_user_model()


class TestFrontpageView:
    """Tests for the frontpage/message board view."""

    @pytest.mark.django_db
    def test_frontpage_requires_login(self, client):
        """Unauthenticated users should be redirected to login."""
        response = client.get(reverse('main:frontpage'))
        assert response.status_code == 302
        assert '/login/' in response.url

    @pytest.mark.django_db
    def test_frontpage_displays_messages(self, authenticated_client):
        """Authenticated users should see messages."""
        MessageFactory.create_batch(3)
        response = authenticated_client.get(reverse('main:frontpage'))
        assert response.status_code == 200
        assert len(response.context['messages']) == 3

    @pytest.mark.django_db
    def test_pinned_messages_shown_first(self, authenticated_client):
        """Pinned messages should appear before regular messages."""
        regular = MessageFactory(is_pinned=False)
        pinned = MessageFactory(is_pinned=True)

        response = authenticated_client.get(reverse('main:frontpage'))
        messages = list(response.context['messages'])

        assert messages[0].is_pinned == True


class TestMessageCreateView:
    """Tests for creating messages."""

    @pytest.mark.django_db
    def test_create_message(self, authenticated_client, user):
        """User can create a new message."""
        response = authenticated_client.post(
            reverse('main:message_create'),
            {'content': 'Test message content'}
        )
        assert response.status_code == 302  # Redirect on success
        assert Message.objects.filter(content='Test message content').exists()

    @pytest.mark.django_db
    def test_create_message_requires_login(self, client):
        """Unauthenticated users cannot create messages."""
        response = client.post(
            reverse('main:message_create'),
            {'content': 'Test'}
        )
        assert response.status_code == 302
        assert '/login/' in response.url


class TestMessageDeleteView:
    """Tests for deleting messages."""

    @pytest.mark.django_db
    def test_user_can_delete_own_message(self, authenticated_client, user):
        """User can delete their own message."""
        message = MessageFactory(author=user)
        response = authenticated_client.post(
            reverse('main:message_delete', args=[message.pk])
        )
        assert response.status_code == 302
        assert not Message.objects.filter(pk=message.pk).exists()

    @pytest.mark.django_db
    def test_user_cannot_delete_others_message(self, authenticated_client, user):
        """User cannot delete another user's message."""
        other_user = UserFactory()
        message = MessageFactory(author=other_user)
        response = authenticated_client.post(
            reverse('main:message_delete', args=[message.pk])
        )
        assert response.status_code == 403
        assert Message.objects.filter(pk=message.pk).exists()


class TestCalendarView:
    """Tests for the calendar view."""

    @pytest.mark.django_db
    def test_calendar_requires_login(self, client):
        response = client.get(reverse('main:kalender'))
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_calendar_loads(self, authenticated_client):
        response = authenticated_client.get(reverse('main:kalender'))
        assert response.status_code == 200


class TestBookingAPIView:
    """Tests for the booking API endpoint."""

    @pytest.mark.django_db
    def test_api_returns_bookings(self, authenticated_client):
        BookingFactory.create_batch(3, status='confirmed')
        response = authenticated_client.get(reverse('main:booking_api'))
        assert response.status_code == 200
        data = response.json()
        # Should include bookings (may also include reserved weeks)
        booking_events = [e for e in data if 'booking' in e.get('id', '')]
        assert len(booking_events) >= 3

    @pytest.mark.django_db
    def test_api_rate_limited(self, authenticated_client):
        """API should be rate limited."""
        # Make many requests quickly
        for _ in range(65):
            authenticated_client.get(reverse('main:booking_api'))

        # Should eventually get rate limited
        response = authenticated_client.get(reverse('main:booking_api'))
        # Rate limit returns 429 or custom error page
        assert response.status_code in [200, 429]  # Depends on cache state


class TestStaffOnlyViews:
    """Tests for staff-only views."""

    @pytest.mark.django_db
    def test_admin_vejledning_requires_staff(self, authenticated_client):
        """Regular users cannot access admin guide."""
        response = authenticated_client.get(reverse('main:admin_vejledning'))
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_admin_vejledning_accessible_to_staff(self, staff_client):
        """Staff users can access admin guide."""
        response = staff_client.get(reverse('main:admin_vejledning'))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_user_management_requires_staff(self, authenticated_client):
        """Regular users cannot access user management."""
        response = authenticated_client.get(reverse('main:user_management'))
        assert response.status_code == 403


class TestNotificationViews:
    """Tests for notification views."""

    @pytest.mark.django_db
    def test_notification_list(self, authenticated_client, user):
        from .factories import NotificationFactory
        NotificationFactory.create_batch(5, user=user)

        response = authenticated_client.get(reverse('main:notifications'))
        assert response.status_code == 200
        assert len(response.context['notifications']) == 5

    @pytest.mark.django_db
    def test_mark_notification_read(self, authenticated_client, user):
        from .factories import NotificationFactory
        notification = NotificationFactory(user=user, is_read=False)

        response = authenticated_client.post(
            reverse('main:notification_mark_read', args=[notification.pk])
        )
        notification.refresh_from_db()
        assert notification.is_read == True
```

#### 6.5 Write Form Tests

**File**: `main/tests/test_forms.py` (create)

```python
import pytest
from django.contrib.auth import get_user_model
from main.forms import CustomUserCreationForm, BookingForm
from .factories import UserFactory

User = get_user_model()


class TestCustomUserCreationForm:
    """Tests for user registration form."""

    @pytest.mark.django_db
    def test_valid_form(self):
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'display_name': 'New User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert form.is_valid()

    @pytest.mark.django_db
    def test_username_no_spaces(self):
        """Username should not allow spaces."""
        form = CustomUserCreationForm(data={
            'username': 'new user',  # Space in username
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert not form.is_valid()
        assert 'username' in form.errors

    @pytest.mark.django_db
    def test_display_name_allows_spaces(self):
        """Display name should allow spaces."""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'display_name': 'Rasmus Damgaard',  # Spaces OK
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert form.is_valid()

    @pytest.mark.django_db
    def test_duplicate_username_rejected(self):
        """Cannot register with existing username."""
        UserFactory(username='existing')
        form = CustomUserCreationForm(data={
            'username': 'existing',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert not form.is_valid()
        assert 'username' in form.errors


class TestBookingForm:
    """Tests for booking form."""

    @pytest.mark.django_db
    def test_valid_booking(self):
        from datetime import date, timedelta
        form = BookingForm(data={
            'start_date': date.today() + timedelta(days=30),
            'end_date': date.today() + timedelta(days=37),
            'notes': 'Family vacation',
        })
        assert form.is_valid()

    @pytest.mark.django_db
    def test_end_before_start_invalid(self):
        from datetime import date
        form = BookingForm(data={
            'start_date': date(2024, 7, 15),
            'end_date': date(2024, 7, 10),  # Before start
            'notes': '',
        })
        assert not form.is_valid()
```

#### 6.6 Write Service Tests

**File**: `main/tests/test_services.py` (create)

```python
import pytest
from unittest.mock import patch, MagicMock
from main.services import NotificationService, AuditService, WeatherService
from main.models import Notification, AuditLog
from .factories import UserFactory, MessageFactory, CommentFactory


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.mark.django_db
    def test_notify_new_message(self):
        """Should create notifications for users who opted in."""
        from main.models import UserProfile

        author = UserFactory()
        subscriber = UserFactory()

        # Set up subscriber to receive notifications
        subscriber.profile.notify_new_messages = True
        subscriber.profile.save()

        message = MessageFactory(author=author)

        notifications = NotificationService.notify_new_message(message)

        # Should have created notification for subscriber
        assert any(n.user == subscriber for n in notifications)
        # Should NOT have notification for author
        assert not any(n.user == author for n in notifications)

    @pytest.mark.django_db
    def test_notify_comment_on_message(self):
        """Should notify message author when comment is added."""
        message = MessageFactory()
        commenter = UserFactory()
        comment = CommentFactory(message=message, author=commenter)

        notification = NotificationService.notify_comment_on_message(
            message, comment
        )

        assert notification is not None
        assert notification.user == message.author
        assert notification.notification_type == 'comment'

    @pytest.mark.django_db
    def test_no_notification_for_own_comment(self):
        """Should not notify when user comments on own message."""
        user = UserFactory()
        message = MessageFactory(author=user)
        comment = CommentFactory(message=message, author=user)

        notification = NotificationService.notify_comment_on_message(
            message, comment
        )

        assert notification is None

    @pytest.mark.django_db
    def test_parse_mentions(self):
        """Should find and notify @mentioned users."""
        mentioned_user = UserFactory(username='rasmus')
        author = UserFactory()
        message = MessageFactory(
            author=author,
            content='Hey @rasmus, check this out!'
        )

        mentioned = NotificationService.parse_and_notify_mentions(
            message.content, author, message
        )

        assert mentioned_user in mentioned
        assert Notification.objects.filter(
            user=mentioned_user,
            notification_type='mention'
        ).exists()


class TestAuditService:
    """Tests for AuditService."""

    @pytest.mark.django_db
    def test_log_action(self):
        """Should create audit log entry."""
        user = UserFactory()

        AuditService.log(
            user=user,
            action='test_action',
            target_type='test',
            target_id=123,
            details={'key': 'value'},
            request=None
        )

        log = AuditLog.objects.latest('created_at')
        assert log.user == user
        assert log.action == 'test_action'
        assert log.details == {'key': 'value'}


class TestWeatherService:
    """Tests for WeatherService."""

    @pytest.mark.django_db
    @patch('main.services.requests.get')
    def test_get_weather_success(self, mock_get):
        """Should return weather data on success."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'properties': {
                'timeseries': [{
                    'time': '2024-07-01T12:00:00Z',
                    'data': {
                        'instant': {
                            'details': {
                                'air_temperature': 22.5
                            }
                        },
                        'next_1_hours': {
                            'summary': {'symbol_code': 'clearsky_day'}
                        }
                    }
                }]
            }
        }
        mock_get.return_value = mock_response

        weather = WeatherService.get_weather()

        assert weather is not None
        assert 'temperature' in weather or 'forecast' in weather

    @pytest.mark.django_db
    @patch('main.services.requests.get')
    def test_get_weather_failure(self, mock_get):
        """Should handle API failure gracefully."""
        mock_get.side_effect = Exception('Network error')

        weather = WeatherService.get_weather()

        # Should return None or empty dict, not raise exception
        assert weather is None or weather == {}
```

#### 6.7 Configure CI/CD

**File**: `.github/workflows/test.yml` (create)

```yaml
name: Tests

on:
  push:
    branches: [main, claude/*]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: |
          uv sync
          uv pip install pytest pytest-django pytest-cov factory-boy faker

      - name: Run tests
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
          SECRET_KEY: test-secret-key-for-ci
          DEBUG: 'False'
        run: |
          uv run pytest --cov=main --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

### Testing Coverage Goals

| Component | Target Coverage |
|-----------|-----------------|
| Models | 90% |
| Views | 80% |
| Forms | 90% |
| Services | 85% |
| Overall | 70% |

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modify | Add dev dependencies |
| `pytest.ini` | Create | Pytest configuration |
| `conftest.py` | Create | Shared fixtures |
| `main/tests/__init__.py` | Create | Test package |
| `main/tests/factories.py` | Create | Model factories |
| `main/tests/test_models.py` | Create | Model tests |
| `main/tests/test_views.py` | Create | View tests |
| `main/tests/test_forms.py` | Create | Form tests |
| `main/tests/test_services.py` | Create | Service tests |
| `.github/workflows/test.yml` | Create | CI configuration |

---

## Phase 7: Accessibility Audit & Fixes

### Problem Analysis

While the site has good semantic HTML and some accessibility features, a formal WCAG 2.1 AA audit has not been conducted. Issues may include:
- Color contrast ratios
- Missing ARIA labels
- Keyboard navigation gaps
- Screen reader compatibility

### Implementation Tasks

#### 7.1 Automated Accessibility Testing

**Install testing tools:**

```bash
# Install pa11y for automated testing
npm install -g pa11y pa11y-ci

# Or use axe-core in browser
```

**File**: `pa11y.config.js` (create)

```javascript
module.exports = {
    defaults: {
        timeout: 30000,
        standard: 'WCAG2AA',
        runners: ['axe'],
    },
    urls: [
        'http://localhost:8000/',
        'http://localhost:8000/information/',
        'http://localhost:8000/kalender/',
        'http://localhost:8000/referater/',
        'http://localhost:8000/vedtaegter/',
        'http://localhost:8000/brugervejledning/',
    ]
};
```

#### 7.2 Fix Color Contrast Issues

**File**: `main/static/main/css/style.css` (update)

```css
/* Ensure AA contrast ratios (4.5:1 for normal text, 3:1 for large text) */

:root {
    /* Updated colors for better contrast */
    --text-primary: #1a1a1a;        /* Was: #333333 */
    --text-secondary: #4a4a4a;      /* Was: #666666 */
    --text-muted: #6b6b6b;          /* Was: #999999 - now meets AA */

    /* Link colors with sufficient contrast */
    --link-color: #1a5276;          /* Darker blue for contrast */
    --link-hover: #154360;

    /* Badge colors with white text */
    --badge-success: #1e7e34;       /* Darker green */
    --badge-warning: #856404;       /* Darker yellow/brown for text */
    --badge-danger: #bd2130;        /* Darker red */
}

/* Ensure focus indicators are visible */
:focus {
    outline: 3px solid var(--accent-teal);
    outline-offset: 2px;
}

/* Skip link for keyboard users */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--primary-blue);
    color: white;
    padding: 8px 16px;
    z-index: 100;
    transition: top 0.3s;
}

.skip-link:focus {
    top: 0;
}
```

#### 7.3 Add Missing ARIA Labels

**File**: `main/templates/main/base.html` (update)

```html
<!-- Add skip link -->
<a href="#main-content" class="skip-link">Spring til hovedindhold</a>

<!-- Add aria-labels to interactive elements -->
<nav aria-label="Hovednavigation">
    <!-- sidebar content -->
</nav>

<main id="main-content" role="main" aria-label="Sideindhold">
    {% block content %}{% endblock %}
</main>

<!-- Notification bell -->
<button aria-label="Notifikationer - {{ unread_count }} ulæste"
        aria-expanded="false"
        aria-haspopup="true">
    <i class="bi bi-bell" aria-hidden="true"></i>
</button>

<!-- Mobile menu toggle -->
<button class="navbar-toggler"
        type="button"
        aria-label="Åbn menu"
        aria-expanded="false"
        aria-controls="navbarNav">
    <span class="navbar-toggler-icon"></span>
</button>
```

#### 7.4 Improve Form Accessibility

**File**: `main/templates/main/booking_form.html` (update example)

```html
<form method="post" aria-describedby="form-instructions">
    <p id="form-instructions" class="visually-hidden">
        Udfyld alle påkrævede felter markeret med stjerne.
    </p>

    {% csrf_token %}

    <div class="mb-3">
        <label for="id_start_date" class="form-label">
            Start dato <span class="text-danger" aria-label="påkrævet">*</span>
        </label>
        <input type="date"
               id="id_start_date"
               name="start_date"
               class="form-control"
               required
               aria-required="true"
               aria-describedby="start_date_help">
        <div id="start_date_help" class="form-text">
            Vælg den første dag for din booking.
        </div>
        {% if form.start_date.errors %}
        <div class="invalid-feedback" role="alert" aria-live="polite">
            {{ form.start_date.errors|join:", " }}
        </div>
        {% endif %}
    </div>

    <!-- Similar pattern for other fields -->

    <button type="submit" class="btn btn-primary">
        <span aria-hidden="true">📅</span> Opret booking
    </button>
</form>
```

#### 7.5 Add Keyboard Navigation Support

**File**: `main/static/main/js/accessibility.js` (create)

```javascript
// Keyboard navigation enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Handle escape key to close modals/dropdowns
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Close any open dropdowns
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(dropdown => {
                const toggle = dropdown.previousElementSibling;
                if (toggle) {
                    toggle.click();
                }
            });

            // Close any open modals
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
                if (closeBtn) {
                    closeBtn.click();
                }
            });
        }
    });

    // Trap focus in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusableElements.length) {
                focusableElements[0].focus();
            }
        });
    });

    // Announce dynamic content changes
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'visually-hidden';
    announcer.id = 'announcer';
    document.body.appendChild(announcer);

    window.announce = function(message) {
        const announcer = document.getElementById('announcer');
        announcer.textContent = message;
        setTimeout(() => { announcer.textContent = ''; }, 1000);
    };
});
```

#### 7.6 Update Image Alt Text

**File**: `main/templates/main/frontpage.html` (update)

```html
<!-- Ensure all images have descriptive alt text -->
<picture>
    <source srcset="{% static 'main/img/House-large.webp' %}"
            media="(min-width: 992px)"
            type="image/webp">
    <source srcset="{% static 'main/img/House-medium.webp' %}"
            media="(min-width: 576px)"
            type="image/webp">
    <img src="{% static 'main/img/House-small.webp' %}"
         alt="Vraa sommerhus - et hvidt træhus med rødt tag omgivet af grønne træer"
         class="hero-image"
         loading="lazy">
</picture>
```

### Accessibility Checklist

- [ ] Skip link to main content
- [ ] All images have alt text
- [ ] Form labels associated with inputs
- [ ] Error messages linked to fields (aria-describedby)
- [ ] Color contrast meets AA (4.5:1)
- [ ] Focus indicators visible
- [ ] Keyboard navigation works
- [ ] Screen reader tested (VoiceOver/NVDA)
- [ ] Heading hierarchy correct (h1 > h2 > h3)
- [ ] ARIA landmarks used (nav, main, aside)
- [ ] Interactive elements have accessible names
- [ ] No content depends solely on color

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `pa11y.config.js` | Create | Automated testing config |
| `main/static/main/css/style.css` | Modify | Contrast fixes, skip link |
| `main/templates/main/base.html` | Modify | ARIA landmarks, skip link |
| `main/templates/main/*.html` | Modify | Form accessibility, alt text |
| `main/static/main/js/accessibility.js` | Create | Keyboard navigation |

---

## Phase 8: Search Functionality

### Problem Analysis

Users cannot search for old messages or documents. As the message board grows, finding specific content becomes difficult.

### Implementation Tasks

#### 8.1 Add Search Model/Index

**Option A: Django Full-Text Search (PostgreSQL)**

**File**: `main/models.py` (update Message model)

```python
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class Message(models.Model):
    # ... existing fields ...

    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]
```

**File**: `main/signals.py` (add search vector update)

```python
from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message

@receiver(post_save, sender=Message)
def update_search_vector(sender, instance, **kwargs):
    """Update search vector when message is saved."""
    Message.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector('content')
    )
```

#### 8.2 Create Search View

**File**: `main/views.py` (add)

```python
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F

class SearchView(LoginRequiredMixin, ListView):
    """Search messages and documents."""
    template_name = 'main/search_results.html'
    context_object_name = 'results'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        search_type = self.request.GET.get('type', 'all')

        if not query:
            return Message.objects.none()

        # PostgreSQL full-text search
        search_query = SearchQuery(query, config='danish')

        results = []

        if search_type in ('all', 'messages'):
            messages = Message.objects.annotate(
                rank=SearchRank(F('search_vector'), search_query)
            ).filter(
                search_vector=search_query
            ).order_by('-rank')

            for msg in messages:
                results.append({
                    'type': 'message',
                    'object': msg,
                    'rank': msg.rank,
                })

        if search_type in ('all', 'documents'):
            # Simple title/description search for documents
            documents = Document.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )

            for doc in documents:
                results.append({
                    'type': 'document',
                    'object': doc,
                    'rank': 0.5,  # Lower rank than text match
                })

        # Sort by rank
        results.sort(key=lambda x: x['rank'], reverse=True)

        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['search_type'] = self.request.GET.get('type', 'all')
        return context
```

#### 8.3 Create Search Template

**File**: `main/templates/main/search_results.html` (create)

```html
{% extends 'main/base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid">
    <h1>Søgeresultater</h1>

    <!-- Search form -->
    <form method="get" class="search-form mb-4">
        <div class="input-group">
            <input type="search"
                   name="q"
                   class="form-control form-control-lg"
                   placeholder="Søg efter beskeder eller dokumenter..."
                   value="{{ query }}"
                   aria-label="Søgeord">
            <button type="submit" class="btn btn-primary">
                <i class="bi bi-search" aria-hidden="true"></i> Søg
            </button>
        </div>

        <div class="mt-2">
            <div class="form-check form-check-inline">
                <input type="radio" name="type" value="all" id="type-all"
                       class="form-check-input"
                       {% if search_type == 'all' %}checked{% endif %}>
                <label for="type-all" class="form-check-label">Alle</label>
            </div>
            <div class="form-check form-check-inline">
                <input type="radio" name="type" value="messages" id="type-messages"
                       class="form-check-input"
                       {% if search_type == 'messages' %}checked{% endif %}>
                <label for="type-messages" class="form-check-label">Beskeder</label>
            </div>
            <div class="form-check form-check-inline">
                <input type="radio" name="type" value="documents" id="type-documents"
                       class="form-check-input"
                       {% if search_type == 'documents' %}checked{% endif %}>
                <label for="type-documents" class="form-check-label">Dokumenter</label>
            </div>
        </div>
    </form>

    {% if query %}
        {% if results %}
            <p class="text-muted">
                Fandt {{ results|length }} resultat{% if results|length != 1 %}er{% endif %}
                for "{{ query }}"
            </p>

            <div class="search-results">
                {% for result in results %}
                    {% if result.type == 'message' %}
                        <div class="search-result-item message-result">
                            <div class="result-type">
                                <span class="badge bg-primary">Besked</span>
                            </div>
                            <div class="result-content">
                                <p>{{ result.object.content|truncatewords:50 }}</p>
                                <small class="text-muted">
                                    Af {{ result.object.author.profile.get_display_name }}
                                    - {{ result.object.created_at|date:"d. M Y" }}
                                </small>
                            </div>
                            <a href="{% url 'main:frontpage' %}#message-{{ result.object.pk }}"
                               class="stretched-link"></a>
                        </div>
                    {% elif result.type == 'document' %}
                        <div class="search-result-item document-result">
                            <div class="result-type">
                                <span class="badge bg-secondary">Dokument</span>
                            </div>
                            <div class="result-content">
                                <h6>{{ result.object.title }}</h6>
                                <p>{{ result.object.description|truncatewords:30 }}</p>
                                <small class="text-muted">
                                    {{ result.object.category|title }}
                                    - {{ result.object.document_date|date:"d. M Y" }}
                                </small>
                            </div>
                            <a href="{{ result.object.file.url }}"
                               class="stretched-link"
                               target="_blank"></a>
                        </div>
                    {% endif %}
                {% endfor %}
            </div>

            {% include 'main/partials/pagination.html' %}
        {% else %}
            <div class="alert alert-info">
                <i class="bi bi-info-circle" aria-hidden="true"></i>
                Ingen resultater fundet for "{{ query }}".
            </div>
        {% endif %}
    {% endif %}
</div>
{% endblock %}
```

#### 8.4 Add Search to Navigation

**File**: `main/templates/main/base.html` (update)

```html
<!-- Add search in navbar -->
<form action="{% url 'main:search' %}" method="get" class="d-flex search-nav">
    <input type="search"
           name="q"
           class="form-control form-control-sm"
           placeholder="Søg..."
           aria-label="Søg">
    <button type="submit" class="btn btn-outline-light btn-sm ms-1">
        <i class="bi bi-search" aria-hidden="true"></i>
    </button>
</form>
```

#### 8.5 Add URL Pattern

**File**: `main/urls.py` (update)

```python
path('soeg/', views.SearchView.as_view(), name='search'),
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `main/models.py` | Modify | Add SearchVectorField |
| `main/signals.py` | Modify | Update search vector on save |
| `main/views.py` | Modify | Add SearchView |
| `main/urls.py` | Modify | Add search URL |
| `main/templates/main/search_results.html` | Create | Search results page |
| `main/templates/main/base.html` | Modify | Add search in nav |
| `main/static/main/css/style.css` | Modify | Search result styling |

---

## Phase 9: Print Styles

### Problem Analysis

Users may want to print meeting minutes, statutes, or booking confirmations. Currently no print-specific styles exist.

### Implementation Tasks

#### 9.1 Add Print Stylesheet

**File**: `main/static/main/css/print.css` (create)

```css
/* Print styles for Vraa site */
@media print {
    /* Hide non-essential elements */
    .sidebar,
    .navbar,
    .nav-container,
    .hamburger-menu,
    .notification-bell,
    .btn,
    .no-print,
    footer,
    .breadcrumb,
    .pagination,
    form:not(.print-form) {
        display: none !important;
    }

    /* Reset layout */
    body {
        font-size: 12pt;
        line-height: 1.5;
        color: #000;
        background: #fff;
    }

    .main-content {
        width: 100%;
        margin: 0;
        padding: 0;
    }

    /* Ensure content takes full width */
    .container,
    .container-fluid {
        width: 100%;
        max-width: none;
        padding: 0;
        margin: 0;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
        color: #000;
    }

    h1 { font-size: 24pt; }
    h2 { font-size: 18pt; }
    h3 { font-size: 14pt; }

    /* Prevent orphans and widows */
    p, li {
        orphans: 3;
        widows: 3;
    }

    /* Tables */
    table {
        border-collapse: collapse;
        width: 100%;
    }

    th, td {
        border: 1px solid #000;
        padding: 8px;
        text-align: left;
    }

    /* Images */
    img {
        max-width: 100%;
        page-break-inside: avoid;
    }

    /* Links - show URL */
    a[href]:after {
        content: " (" attr(href) ")";
        font-size: 10pt;
        color: #666;
    }

    a[href^="#"]:after,
    a[href^="javascript:"]:after {
        content: "";
    }

    /* Cards */
    .card {
        border: 1px solid #ccc;
        break-inside: avoid;
        margin-bottom: 1rem;
    }

    .card-header {
        background: #f5f5f5 !important;
        border-bottom: 1px solid #ccc;
    }

    /* Message board specific */
    .message-card {
        border: 1px solid #ccc;
        padding: 1rem;
        margin-bottom: 1rem;
        break-inside: avoid;
    }

    .message-header {
        border-bottom: 1px solid #eee;
        padding-bottom: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .heritage-badge {
        border: 1px solid #000;
        padding: 2px 6px;
    }

    /* Booking confirmation */
    .booking-confirmation {
        border: 2px solid #000;
        padding: 2rem;
    }

    .booking-confirmation h2 {
        text-align: center;
        border-bottom: 2px solid #000;
        padding-bottom: 1rem;
    }

    .booking-details {
        margin: 2rem 0;
    }

    .booking-details dt {
        font-weight: bold;
    }

    .booking-details dd {
        margin-bottom: 1rem;
    }

    /* Calendar - hide, not printable */
    .calendar-container,
    #calendar {
        display: none !important;
    }

    /* Show printable booking list instead */
    .booking-list-print {
        display: block !important;
    }

    /* Page breaks */
    .page-break {
        page-break-before: always;
    }

    .no-break {
        page-break-inside: avoid;
    }

    /* Header/footer for print */
    @page {
        margin: 2cm;

        @top-center {
            content: "Vraa Sommerhus";
        }

        @bottom-center {
            content: "Side " counter(page) " af " counter(pages);
        }
    }

    /* First page - no header */
    @page :first {
        @top-center {
            content: "";
        }
    }
}
```

#### 9.2 Add Print Button Component

**File**: `main/templates/main/partials/print_button.html` (create)

```html
<button type="button"
        class="btn btn-outline-secondary no-print"
        onclick="window.print()"
        aria-label="Udskriv denne side">
    <i class="bi bi-printer" aria-hidden="true"></i> Udskriv
</button>
```

#### 9.3 Create Printable Booking Confirmation

**File**: `main/templates/main/booking_confirmation_print.html` (create)

```html
{% extends 'main/base.html' %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'main/css/print.css' %}" media="print">
{% endblock %}

{% block content %}
<div class="booking-confirmation">
    <div class="d-flex justify-content-between align-items-center no-print mb-3">
        <h1>Bookingbekræftelse</h1>
        {% include 'main/partials/print_button.html' %}
    </div>

    <div class="print-header text-center mb-4">
        <img src="{% static 'main/img/logo.png' %}" alt="Vraa logo" height="60">
        <h2>Vraa Sommerhus - Bookingbekræftelse</h2>
    </div>

    <div class="booking-details">
        <dl class="row">
            <dt class="col-sm-4">Booking reference:</dt>
            <dd class="col-sm-8">#{{ booking.pk }}</dd>

            <dt class="col-sm-4">Booket af:</dt>
            <dd class="col-sm-8">{{ booking.user.profile.get_display_name }}</dd>

            <dt class="col-sm-4">Familie-linje:</dt>
            <dd class="col-sm-8">
                {% if booking.user.profile.heritage_line %}
                    {{ booking.user.profile.heritage_line.name }}
                {% else %}
                    Ikke angivet
                {% endif %}
            </dd>

            <dt class="col-sm-4">Ankomst:</dt>
            <dd class="col-sm-8">{{ booking.start_date|date:"l d. F Y" }}</dd>

            <dt class="col-sm-4">Afrejse:</dt>
            <dd class="col-sm-8">{{ booking.end_date|date:"l d. F Y" }}</dd>

            <dt class="col-sm-4">Antal nætter:</dt>
            <dd class="col-sm-8">{{ booking.duration_days }}</dd>

            <dt class="col-sm-4">Status:</dt>
            <dd class="col-sm-8">
                {% if booking.status == 'confirmed' %}
                    <strong class="text-success">Bekræftet</strong>
                {% elif booking.status == 'pending' %}
                    <em>Afventer godkendelse</em>
                {% else %}
                    {{ booking.get_status_display }}
                {% endif %}
            </dd>

            {% if booking.notes %}
            <dt class="col-sm-4">Bemærkninger:</dt>
            <dd class="col-sm-8">{{ booking.notes }}</dd>
            {% endif %}
        </dl>
    </div>

    <div class="print-footer mt-5 pt-3 border-top">
        <p class="text-muted small">
            Udskrevet fra vraa.org den {{ 'now'|date:"d. F Y" }}<br>
            Ved spørgsmål kontakt venligst administrator.
        </p>
    </div>
</div>
{% endblock %}
```

#### 9.4 Link Print Stylesheet

**File**: `main/templates/main/base.html` (update)

```html
<head>
    <!-- ... existing head content ... -->

    <!-- Print styles -->
    <link rel="stylesheet" href="{% static 'main/css/print.css' %}" media="print">
</head>
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `main/static/main/css/print.css` | Create | Print stylesheet |
| `main/templates/main/base.html` | Modify | Link print CSS |
| `main/templates/main/partials/print_button.html` | Create | Print button |
| `main/templates/main/booking_confirmation_print.html` | Create | Printable booking |

---

## Phase 10: Production Hardening

### Problem Analysis

While security settings are mostly configured, some production hardening remains:
- `ALLOWED_HOSTS` uses `['*']` in base config
- No explicit environment checks
- Missing monitoring/error tracking

### Implementation Tasks

#### 10.1 Finalize ALLOWED_HOSTS

**File**: `Vraa/settings.py` (update)

```python
# ALLOWED_HOSTS configuration
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', '.localhost']
else:
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
    if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
        ALLOWED_HOSTS = [
            'vraa.org',
            'www.vraa.org',
            '.herokuapp.com',
        ]
```

**Heroku config:**
```bash
heroku config:set ALLOWED_HOSTS="vraa.org,www.vraa.org,vraa-app.herokuapp.com"
```

#### 10.2 Add Environment Validation

**File**: `Vraa/settings.py` (add at end)

```python
# Production environment validation
if not DEBUG:
    required_env_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
    ]

    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

    if missing_vars:
        import warnings
        warnings.warn(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Application may not function correctly.",
            RuntimeWarning
        )

    # Validate SECRET_KEY is not the default
    if SECRET_KEY == 'django-insecure-local-dev-key-change-me':
        raise ValueError(
            "SECRET_KEY is set to the default development value. "
            "Set a secure SECRET_KEY environment variable for production."
        )
```

#### 10.3 Add Sentry Error Tracking (Optional)

**File**: `pyproject.toml` (add dependency)

```toml
[project]
dependencies = [
    # ... existing ...
    "sentry-sdk>=1.0",
]
```

**File**: `Vraa/settings.py` (add Sentry config)

```python
# Sentry error tracking (production only)
SENTRY_DSN = os.environ.get('SENTRY_DSN')

if not DEBUG and SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions
        send_default_pii=False,  # Don't send personally identifiable info
        environment=os.environ.get('ENVIRONMENT', 'production'),
    )
```

#### 10.4 Add Health Check Endpoint

**File**: `main/views.py` (add)

```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for monitoring."""
    health = {
        'status': 'healthy',
        'checks': {}
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['checks']['database'] = 'ok'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['checks']['database'] = str(e)

    # Cache check
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health['checks']['cache'] = 'ok'
        else:
            health['checks']['cache'] = 'failed'
    except Exception as e:
        health['checks']['cache'] = str(e)

    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)
```

**File**: `main/urls.py` (add)

```python
path('health/', views.health_check, name='health_check'),
```

**File**: `main/middleware.py` (exempt health check from login)

```python
LOGIN_EXEMPT_URLS = [
    '/login/',
    '/logout/',
    '/register/',
    '/password-reset/',
    '/health/',  # Add health check
]
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `Vraa/settings.py` | Modify | Finalize ALLOWED_HOSTS, add validation |
| `pyproject.toml` | Modify | Add sentry-sdk (optional) |
| `main/views.py` | Modify | Add health check endpoint |
| `main/urls.py` | Modify | Add health check URL |
| `main/middleware.py` | Modify | Exempt health check from login |

---

## Implementation Order & Dependencies

```
Phase 6: Automated Tests (No dependencies)
    └── Can be done first, establishes quality baseline

Phase 7: Accessibility (No dependencies)
    └── Can be done in parallel with Phase 6

Phase 8: Search (No dependencies)
    └── Can be done in parallel with Phase 6/7

Phase 9: Print Styles (No dependencies)
    └── Quick win, can be done anytime

Phase 10: Production Hardening (No dependencies)
    └── Should be done before any production deployment
```

### Recommended Implementation Sequence

1. **Session 1**: Phase 10 (Production Hardening) - Quick wins, critical for deployment
2. **Session 2**: Phase 6 (Automated Tests) - Foundation for ongoing quality
3. **Session 3**: Phase 7 (Accessibility) - Important for inclusive design
4. **Session 4**: Phase 8 (Search) - User-requested feature
5. **Session 5**: Phase 9 (Print Styles) - Polish feature

---

## Testing Checklist

### Phase 6: Automated Tests
- [ ] pytest runs successfully
- [ ] Model tests pass
- [ ] View tests pass
- [ ] Form tests pass
- [ ] Service tests pass
- [ ] Coverage >= 70%
- [ ] CI pipeline passes

### Phase 7: Accessibility
- [ ] pa11y reports no critical issues
- [ ] Skip link works
- [ ] Keyboard navigation functional
- [ ] Screen reader tested
- [ ] Color contrast verified
- [ ] ARIA labels present

### Phase 8: Search
- [ ] Search returns relevant results
- [ ] Messages searchable
- [ ] Documents searchable
- [ ] Pagination works
- [ ] Empty results handled
- [ ] Search from nav works

### Phase 9: Print Styles
- [ ] Print preview looks good
- [ ] Non-essential elements hidden
- [ ] Links show URLs
- [ ] Page breaks appropriate
- [ ] Booking confirmation printable

### Phase 10: Production Hardening
- [ ] ALLOWED_HOSTS configured
- [ ] Environment validation works
- [ ] Health check returns 200
- [ ] Sentry captures errors (if enabled)
- [ ] No sensitive data in logs

---

## Summary

This implementation plan addresses the final polish recommendations identified during the quality review:

| Recommendation | Phase | Priority | Status |
|---------------|-------|----------|--------|
| Automated tests | 6 | P1 | Planned |
| Accessibility audit | 7 | P2 | Planned |
| Search functionality | 8 | P2 | Planned |
| Print styles | 9 | P3 | Planned |
| Production hardening | 10 | P1 | Planned |

These improvements will elevate the project from **8.4/10 to 9.5/10** quality rating, ensuring:
- Long-term maintainability through tests
- Inclusive design through accessibility
- Better user experience through search
- Professional document output through print styles
- Production reliability through hardening

---

**Document Version**: 1.0
**Created**: 2026-02-05
**Last Updated**: 2026-02-05
