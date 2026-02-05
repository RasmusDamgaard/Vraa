"""
Tests for models in the main application.

Uses pytest-django for database access and factory_boy for test data.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError

from main.models import (
    AuditLog,
    Booking,
    Comment,
    Document,
    HeritageLine,
    MaintenanceRequest,
    Message,
    Notification,
    ReservedWeek,
    UserProfile,
)

from .factories import (
    AuditLogFactory,
    BookingFactory,
    CommentFactory,
    DocumentFactory,
    HeritageLineFactory,
    MaintenanceRequestFactory,
    MessageFactory,
    NotificationFactory,
    ReservedWeekFactory,
    UserFactory,
    UserProfileFactory,
)


# =============================================================================
# HeritageLine Model Tests
# =============================================================================


class TestHeritageLine:
    """Tests for the HeritageLine model."""

    @pytest.mark.django_db
    def test_create_heritage_line(self):
        """A heritage line can be created with valid data."""
        line = HeritageLineFactory(name='Damgaard-linjen', short_name='Damgaard')
        assert line.name == 'Damgaard-linjen'
        assert line.short_name == 'Damgaard'
        assert line.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self):
        """__str__ returns the heritage line name."""
        line = HeritageLineFactory(name='Test Linje')
        assert str(line) == 'Test Linje'

    @pytest.mark.django_db
    def test_ordering_by_order_then_name(self):
        """Heritage lines are ordered by order field, then by name."""
        line3 = HeritageLineFactory(name='C Linje', order=2)
        line1 = HeritageLineFactory(name='A Linje', order=0)
        line2 = HeritageLineFactory(name='B Linje', order=1)

        lines = list(HeritageLine.objects.all())
        assert lines[0] == line1
        assert lines[1] == line2
        assert lines[2] == line3

    @pytest.mark.django_db
    def test_get_reserved_weeks_for_year_base_year(self):
        """Reserved weeks calculation works for base year 2024."""
        # Create 4 heritage lines as expected by the rotation system
        for i in range(4):
            HeritageLineFactory(order=i, base_weeks=[26 + i * 2, 27 + i * 2])

        line = HeritageLine.objects.get(order=0)
        weeks = line.get_reserved_weeks_for_year(2024)
        assert weeks == [26, 27]

    @pytest.mark.django_db
    def test_get_reserved_weeks_rotation(self):
        """Reserved weeks rotate correctly each year."""
        # Create 4 heritage lines
        for i in range(4):
            HeritageLineFactory(order=i, base_weeks=[26 + i * 2, 27 + i * 2])

        line1 = HeritageLine.objects.get(order=0)

        # In 2024, line 1 gets weeks 26-27
        weeks_2024 = line1.get_reserved_weeks_for_year(2024)
        assert weeks_2024 == [26, 27]

        # In 2025, line 1 should rotate to weeks 28-29
        weeks_2025 = line1.get_reserved_weeks_for_year(2025)
        assert weeks_2025 == [28, 29]

    @pytest.mark.django_db
    def test_get_reserved_weeks_empty_base_weeks(self):
        """Returns empty list when base_weeks is empty."""
        line = HeritageLineFactory(base_weeks=[])
        weeks = line.get_reserved_weeks_for_year(2024)
        assert weeks == []

    @pytest.mark.django_db
    def test_unique_name_constraint(self):
        """Heritage line names must be unique."""
        HeritageLineFactory(name='Unique Line')
        with pytest.raises(Exception):  # IntegrityError
            HeritageLineFactory(name='Unique Line')


# =============================================================================
# UserProfile Model Tests
# =============================================================================


class TestUserProfile:
    """Tests for the UserProfile model."""

    @pytest.mark.django_db
    def test_create_user_profile(self):
        """A user profile can be created with valid data."""
        profile = UserProfileFactory(display_name='Rasmus Damgaard')
        assert profile.display_name == 'Rasmus Damgaard'
        assert profile.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self):
        """__str__ returns username's profile."""
        user = UserFactory(username='testuser')
        profile = UserProfileFactory(user=user)
        assert "testuser's profil" in str(profile)

    @pytest.mark.django_db
    def test_get_display_name_with_display_name(self):
        """get_display_name returns display_name when set."""
        profile = UserProfileFactory(display_name='Rasmus Damgaard')
        assert profile.get_display_name() == 'Rasmus Damgaard'

    @pytest.mark.django_db
    def test_get_display_name_fallback_to_username(self):
        """get_display_name returns username when display_name is empty."""
        user = UserFactory(username='testuser')
        profile = UserProfileFactory(user=user, display_name='')
        assert profile.get_display_name() == 'testuser'

    @pytest.mark.django_db
    def test_full_display_name_property(self):
        """full_display_name property is alias for get_display_name."""
        profile = UserProfileFactory(display_name='Test Name')
        assert profile.full_display_name == 'Test Name'

    @pytest.mark.django_db
    def test_default_notification_preferences(self):
        """Default notification preferences are set correctly."""
        user = UserFactory()
        # Profile is auto-created by signal, so just get it
        profile = user.profile
        assert profile.email_notification_pref == 'all'
        assert profile.notify_new_messages is True
        assert profile.notify_comments is True

    @pytest.mark.django_db
    def test_heritage_line_relationship(self):
        """User profile can be linked to a heritage line."""
        line = HeritageLineFactory(name='Test Line')
        user = UserFactory()
        profile = user.profile
        profile.heritage_line = line
        profile.save()
        assert profile.heritage_line == line
        assert profile in line.members.all()


# =============================================================================
# ReservedWeek Model Tests
# =============================================================================


class TestReservedWeek:
    """Tests for the ReservedWeek model."""

    @pytest.mark.django_db
    def test_create_reserved_week(self):
        """A reserved week can be created."""
        line = HeritageLineFactory()
        week = ReservedWeek.objects.create(
            heritage_line=line,
            year=2024,
            week_number=26,
        )
        assert week.pk is not None
        assert week.year == 2024
        assert week.week_number == 26

    @pytest.mark.django_db
    def test_auto_calculate_dates(self):
        """Start and end dates are auto-calculated from year and week."""
        line = HeritageLineFactory()
        week = ReservedWeek.objects.create(
            heritage_line=line,
            year=2024,
            week_number=26,
        )
        assert week.start_date is not None
        assert week.end_date is not None
        assert (week.end_date - week.start_date).days == 6

    @pytest.mark.django_db
    def test_str_representation(self):
        """__str__ returns formatted representation."""
        line = HeritageLineFactory(short_name='DG')
        week = ReservedWeek.objects.create(
            heritage_line=line,
            year=2024,
            week_number=26,
        )
        assert 'DG' in str(week)
        assert '26' in str(week)
        assert '2024' in str(week)

    @pytest.mark.django_db
    def test_generate_for_year(self):
        """generate_for_year creates reserved weeks for all lines."""
        # Create 4 heritage lines with 2 weeks each
        for i in range(4):
            HeritageLineFactory(order=i, base_weeks=[26 + i * 2, 27 + i * 2])

        count = ReservedWeek.generate_for_year(2024)
        assert count == 8  # 4 lines * 2 weeks

    @pytest.mark.django_db
    def test_generate_for_year_idempotent(self):
        """generate_for_year doesn't create duplicates."""
        for i in range(4):
            HeritageLineFactory(order=i, base_weeks=[26 + i * 2, 27 + i * 2])

        count1 = ReservedWeek.generate_for_year(2024)
        count2 = ReservedWeek.generate_for_year(2024)

        assert count1 == 8
        assert count2 == 0  # No new weeks created

    @pytest.mark.django_db
    def test_get_reserved_for_date_range(self):
        """get_reserved_for_date_range returns overlapping weeks."""
        line = HeritageLineFactory()
        week = ReservedWeek.objects.create(
            heritage_line=line,
            year=2024,
            week_number=26,
        )

        # Query with overlapping date range
        results = ReservedWeek.get_reserved_for_date_range(
            week.start_date,
            week.end_date,
        )
        assert week in results

        # Query with non-overlapping date range
        far_future = date(2030, 1, 1)
        results = ReservedWeek.get_reserved_for_date_range(
            far_future,
            far_future + timedelta(days=7),
        )
        assert week not in results

    @pytest.mark.django_db
    def test_unique_together_constraint(self):
        """Cannot create duplicate reserved weeks for same line/year/week."""
        line = HeritageLineFactory()
        ReservedWeek.objects.create(
            heritage_line=line,
            year=2024,
            week_number=26,
        )
        with pytest.raises(Exception):  # IntegrityError
            ReservedWeek.objects.create(
                heritage_line=line,
                year=2024,
                week_number=26,
            )


# =============================================================================
# Notification Model Tests
# =============================================================================


class TestNotification:
    """Tests for the Notification model."""

    @pytest.mark.django_db
    def test_create_notification(self):
        """A notification can be created with valid data."""
        notification = NotificationFactory(
            title='Test Notification',
            notification_type='comment',
        )
        assert notification.title == 'Test Notification'
        assert notification.notification_type == 'comment'
        assert notification.is_read is False

    @pytest.mark.django_db
    def test_str_representation(self):
        """__str__ returns user and title."""
        user = UserFactory(username='testuser')
        notification = NotificationFactory(user=user, title='Test Title')
        str_repr = str(notification)
        assert 'testuser' in str_repr
        assert 'Test Title' in str_repr

    @pytest.mark.django_db
    def test_ordering_by_created_at_descending(self):
        """Notifications are ordered newest first."""
        user = UserFactory()
        n1 = NotificationFactory(user=user)
        n2 = NotificationFactory(user=user)

        notifications = list(Notification.objects.filter(user=user))
        assert notifications[0] == n2  # Newest first
        assert notifications[1] == n1

    @pytest.mark.django_db
    def test_notification_types(self):
        """All notification types can be created."""
        user = UserFactory()
        types = ['comment', 'booking_approved', 'booking_rejected', 'mention', 'reply', 'new_message', 'booking_reminder']

        for ntype in types:
            notification = NotificationFactory(user=user, notification_type=ntype)
            assert notification.notification_type == ntype


# =============================================================================
# Document Model Tests
# =============================================================================


class TestDocument:
    """Tests for the Document model."""

    @pytest.mark.django_db
    def test_str_representation(self):
        """__str__ returns category display and title."""
        doc = DocumentFactory(title='Test Document', category='referat')
        str_repr = str(doc)
        assert 'Referat' in str_repr
        assert 'Test Document' in str_repr

    @pytest.mark.django_db
    def test_ordering_by_document_date_descending(self):
        """Documents are ordered by document_date descending."""
        user = UserFactory()
        doc1 = DocumentFactory(
            uploaded_by=user,
            document_date=date(2020, 1, 1),
        )
        doc2 = DocumentFactory(
            uploaded_by=user,
            document_date=date(2021, 1, 1),
        )

        docs = list(Document.objects.all())
        assert docs[0] == doc2  # Newer first
        assert docs[1] == doc1


# =============================================================================
# MaintenanceRequest Model Tests
# =============================================================================


class TestMaintenanceRequest:
    """Tests for the MaintenanceRequest model."""

    @pytest.mark.django_db
    def test_create_maintenance_request(self):
        """A maintenance request can be created."""
        request = MaintenanceRequestFactory(
            title='Broken window',
            priority='high',
        )
        assert request.title == 'Broken window'
        assert request.priority == 'high'
        assert request.status == 'pending'

    @pytest.mark.django_db
    def test_str_representation(self):
        """__str__ returns title and status."""
        request = MaintenanceRequestFactory(title='Leaky faucet', status='pending')
        str_repr = str(request)
        assert 'Leaky faucet' in str_repr
        assert 'Afventer' in str_repr  # Danish for 'pending'

    @pytest.mark.django_db
    def test_default_status_pending(self):
        """Default status is pending."""
        user = UserFactory()
        request = MaintenanceRequest.objects.create(
            reporter=user,
            title='Test',
            description='Test description',
        )
        assert request.status == 'pending'

    @pytest.mark.django_db
    def test_default_priority_medium(self):
        """Default priority is medium."""
        user = UserFactory()
        request = MaintenanceRequest.objects.create(
            reporter=user,
            title='Test',
            description='Test description',
        )
        assert request.priority == 'medium'


# =============================================================================
# AuditLog Model Tests
# =============================================================================


class TestAuditLog:
    """Tests for the AuditLog model."""

    @pytest.mark.django_db
    def test_create_audit_log(self):
        """An audit log entry can be created."""
        log = AuditLogFactory(
            action='user_activated',
            target_type='User',
            target_id=123,
        )
        assert log.action == 'user_activated'
        assert log.target_type == 'User'
        assert log.target_id == 123

    @pytest.mark.django_db
    def test_str_representation(self):
        """__str__ returns user, action, and timestamp."""
        user = UserFactory(username='testuser')
        log = AuditLogFactory(user=user, action='user_activated')
        str_repr = str(log)
        assert 'testuser' in str_repr
        assert 'Bruger aktiveret' in str_repr  # Danish for action

    @pytest.mark.django_db
    def test_ordering_by_created_at_descending(self):
        """Audit logs are ordered newest first."""
        user = UserFactory()
        log1 = AuditLogFactory(user=user)
        log2 = AuditLogFactory(user=user)

        logs = list(AuditLog.objects.all())
        assert logs[0] == log2  # Newest first
        assert logs[1] == log1

    @pytest.mark.django_db
    def test_details_json_field(self):
        """Details field stores JSON data."""
        log = AuditLogFactory(
            details={'username': 'testuser', 'action': 'test'},
        )
        assert log.details['username'] == 'testuser'
        assert log.details['action'] == 'test'
