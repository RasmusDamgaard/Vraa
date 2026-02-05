"""
Tests for forms in the main application.

Tests for CustomUserCreationForm, UserProfileForm, BookingForm, etc.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from main.forms import BookingForm, CustomUserCreationForm, NotificationPreferencesForm, UserProfileForm
from main.models import Booking, UserProfile

from .factories import BookingFactory, HeritageLineFactory, UserFactory, UserProfileFactory


# =============================================================================
# CustomUserCreationForm Tests
# =============================================================================


class TestCustomUserCreationForm:
    """Tests for user registration form."""

    @pytest.mark.django_db
    def test_valid_form(self):
        """Form is valid with correct data."""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'display_name': 'New User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_username_no_spaces_allowed(self):
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
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_display_name_optional(self):
        """Display name is optional."""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert form.is_valid(), form.errors

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

    @pytest.mark.django_db
    def test_duplicate_username_case_insensitive(self):
        """Username check is case-insensitive."""
        UserFactory(username='ExistingUser')
        form = CustomUserCreationForm(data={
            'username': 'existinguser',  # Different case
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert not form.is_valid()
        assert 'username' in form.errors

    @pytest.mark.django_db
    def test_duplicate_email_rejected(self):
        """Cannot register with existing email."""
        UserFactory(email='existing@example.com')
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    @pytest.mark.django_db
    def test_email_required(self):
        """Email is required."""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': '',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    @pytest.mark.django_db
    def test_password_mismatch(self):
        """Passwords must match."""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass456!',
        })
        assert not form.is_valid()
        assert 'password2' in form.errors

    @pytest.mark.django_db
    def test_save_creates_user(self):
        """Save method creates user with email and profile."""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'display_name': 'New User Display',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert form.is_valid()
        user = form.save()

        assert user.username == 'newuser'
        assert user.email == 'new@example.com'

    @pytest.mark.django_db
    def test_username_special_characters(self):
        """Username can contain @.+-_"""
        form = CustomUserCreationForm(data={
            'username': 'user@test.name-1_2',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        assert form.is_valid(), form.errors


# =============================================================================
# UserProfileForm Tests
# =============================================================================


class TestUserProfileForm:
    """Tests for user profile edit form."""

    @pytest.mark.django_db
    def test_valid_form(self):
        """Form is valid with correct data."""
        form = UserProfileForm(data={
            'display_name': 'Test User',
            'bio': 'This is my bio.',
            'email_notification_pref': 'all',
            'notify_new_messages': True,
            'notify_comments': True,
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_display_name_optional(self):
        """Display name is optional."""
        form = UserProfileForm(data={
            'display_name': '',
            'bio': '',
            'email_notification_pref': 'all',
            'notify_new_messages': True,
            'notify_comments': True,
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_bio_max_length(self):
        """Bio has maximum length of 500 characters."""
        long_bio = 'A' * 501
        form = UserProfileForm(data={
            'display_name': 'Test',
            'bio': long_bio,
            'email_notification_pref': 'all',
            'notify_new_messages': True,
            'notify_comments': True,
        })
        assert not form.is_valid()
        assert 'bio' in form.errors

    @pytest.mark.django_db
    def test_notification_preferences_choices(self):
        """Notification preference must be valid choice."""
        form = UserProfileForm(data={
            'display_name': 'Test',
            'bio': '',
            'email_notification_pref': 'invalid',
            'notify_new_messages': True,
            'notify_comments': True,
        })
        assert not form.is_valid()
        assert 'email_notification_pref' in form.errors

    @pytest.mark.django_db
    def test_form_has_bootstrap_classes(self):
        """Form fields have Bootstrap classes."""
        form = UserProfileForm()
        assert 'form-control' in str(form['display_name'])
        assert 'form-control' in str(form['bio'])
        assert 'form-select' in str(form['email_notification_pref'])


# =============================================================================
# NotificationPreferencesForm Tests
# =============================================================================


class TestNotificationPreferencesForm:
    """Tests for notification preferences form."""

    @pytest.mark.django_db
    def test_valid_form(self):
        """Form is valid with correct data."""
        form = NotificationPreferencesForm(data={
            'email_notification_pref': 'mentions_only',
            'notify_new_messages': False,
            'notify_comments': True,
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_none_preference(self):
        """Can set notification preference to none."""
        form = NotificationPreferencesForm(data={
            'email_notification_pref': 'none',
            'notify_new_messages': False,
            'notify_comments': False,
        })
        assert form.is_valid(), form.errors


# =============================================================================
# BookingForm Tests
# =============================================================================


class TestBookingForm:
    """Tests for booking form."""

    @pytest.fixture
    def future_date(self):
        """Return a function to generate future dates."""
        def _future_date(days=5):
            return date.today() + timedelta(days=days)
        return _future_date

    @pytest.mark.django_db
    def test_valid_form(self, future_date):
        """Form is valid with correct data."""
        form = BookingForm(data={
            'start_date': future_date(5),
            'end_date': future_date(10),
            'notes': 'Family vacation',
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_valid_form_without_notes(self, future_date):
        """Form is valid without notes (optional field)."""
        form = BookingForm(data={
            'start_date': future_date(5),
            'end_date': future_date(10),
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_end_before_start_invalid(self, future_date):
        """Form is invalid when end_date < start_date."""
        form = BookingForm(data={
            'start_date': future_date(10),
            'end_date': future_date(5),  # Before start
        })
        assert not form.is_valid()
        assert 'end_date' in form.errors

    @pytest.mark.django_db
    def test_same_start_and_end_invalid(self, future_date):
        """Form is invalid when start and end are the same."""
        same_date = future_date(5)
        form = BookingForm(data={
            'start_date': same_date,
            'end_date': same_date,
        })
        assert not form.is_valid()

    @pytest.mark.django_db
    def test_overlapping_confirmed_booking_invalid(self, future_date):
        """Form is invalid when overlapping confirmed booking."""
        user = UserFactory()
        BookingFactory(
            user=user,
            start_date=future_date(5),
            end_date=future_date(10),
            status='confirmed',
        )

        form = BookingForm(data={
            'start_date': future_date(7),
            'end_date': future_date(12),
        })
        assert not form.is_valid()

    @pytest.mark.django_db
    def test_overlapping_pending_booking_valid(self, future_date):
        """Form is valid when overlapping pending booking."""
        user = UserFactory()
        BookingFactory(
            user=user,
            start_date=future_date(5),
            end_date=future_date(10),
            status='pending',  # Not confirmed
        )

        form = BookingForm(data={
            'start_date': future_date(7),
            'end_date': future_date(12),
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_adjacent_bookings_valid(self, future_date):
        """Adjacent bookings are valid (one ends when another starts)."""
        user = UserFactory()
        BookingFactory(
            user=user,
            start_date=future_date(5),
            end_date=future_date(10),
            status='confirmed',
        )

        form = BookingForm(data={
            'start_date': future_date(10),
            'end_date': future_date(15),
        })
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_edit_excludes_self_from_overlap_check(self, future_date):
        """When editing, form doesn't flag self as overlap."""
        user = UserFactory()
        booking = BookingFactory(
            user=user,
            start_date=future_date(5),
            end_date=future_date(10),
            status='confirmed',
        )

        # Edit same booking (same dates) - should be valid
        form = BookingForm(
            instance=booking,
            data={
                'start_date': future_date(5),
                'end_date': future_date(10),
            },
        )
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_date_widgets_render_correctly(self):
        """Date fields render with date input type."""
        form = BookingForm()
        assert 'type="date"' in str(form['start_date'])
        assert 'type="date"' in str(form['end_date'])

    @pytest.mark.django_db
    def test_form_has_bootstrap_classes(self):
        """Form fields have Bootstrap form-control class."""
        form = BookingForm()
        assert 'form-control' in str(form['start_date'])
        assert 'form-control' in str(form['end_date'])
        assert 'form-control' in str(form['notes'])
