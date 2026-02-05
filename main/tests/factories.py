"""
Model factories for generating test data.

Uses factory_boy for creating test instances with sensible defaults.
"""
from __future__ import annotations

from datetime import date, timedelta

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

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

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True


class HeritageLineFactory(DjangoModelFactory):
    """Factory for creating HeritageLine instances."""

    class Meta:
        model = HeritageLine

    name = factory.Sequence(lambda n: f'Linje {n}')
    short_name = factory.Sequence(lambda n: f'L{n}')
    description = factory.Faker('paragraph', locale='da_DK')
    color = '#2C5F7C'
    badge_class = 'bg-primary'
    order = factory.Sequence(lambda n: n)
    base_weeks = factory.LazyFunction(lambda: [26, 27])


class UserProfileFactory(DjangoModelFactory):
    """
    Factory for creating/updating UserProfile instances.

    Note: UserProfile is auto-created via signal when User is created,
    so this factory uses get_or_create strategy.
    """

    class Meta:
        model = UserProfile
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    display_name = factory.Faker('name', locale='da_DK')
    bio = factory.Faker('paragraph', locale='da_DK')
    heritage_line = None  # Don't auto-create heritage line by default
    family_role = 'member'
    email_notification_pref = 'all'
    notify_new_messages = True
    notify_comments = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to update existing profile instead of creating."""
        user = kwargs.pop('user', None)
        if user is None:
            user = UserFactory()

        # Get or create the profile (signal should have created it)
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Update with provided values
        for key, value in kwargs.items():
            setattr(profile, key, value)
        profile.save()

        return profile


class MessageFactory(DjangoModelFactory):
    """Factory for creating Message instances."""

    class Meta:
        model = Message

    author = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph', locale='da_DK')
    is_pinned = False


class CommentFactory(DjangoModelFactory):
    """Factory for creating Comment instances."""

    class Meta:
        model = Comment

    message = factory.SubFactory(MessageFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('sentence', locale='da_DK')


class BookingFactory(DjangoModelFactory):
    """Factory for creating Booking instances."""

    class Meta:
        model = Booking

    user = factory.SubFactory(UserFactory)
    start_date = factory.LazyFunction(lambda: date.today() + timedelta(days=10))
    end_date = factory.LazyFunction(lambda: date.today() + timedelta(days=17))
    status = 'pending'
    notes = factory.Faker('sentence', locale='da_DK')


class ReservedWeekFactory(DjangoModelFactory):
    """Factory for creating ReservedWeek instances."""

    class Meta:
        model = ReservedWeek

    heritage_line = factory.SubFactory(HeritageLineFactory)
    year = factory.LazyFunction(lambda: date.today().year)
    week_number = 26
    is_locked = True
    notes = ''


class NotificationFactory(DjangoModelFactory):
    """Factory for creating Notification instances."""

    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    notification_type = 'comment'
    title = factory.Faker('sentence', nb_words=4, locale='da_DK')
    message = factory.Faker('sentence', locale='da_DK')
    link = '/'
    is_read = False


class DocumentFactory(DjangoModelFactory):
    """Factory for creating Document instances."""

    class Meta:
        model = Document

    title = factory.Faker('sentence', nb_words=4, locale='da_DK')
    category = 'referat'
    document_date = factory.LazyFunction(lambda: date.today())
    description = factory.Faker('paragraph', locale='da_DK')
    uploaded_by = factory.SubFactory(UserFactory)


class MaintenanceRequestFactory(DjangoModelFactory):
    """Factory for creating MaintenanceRequest instances."""

    class Meta:
        model = MaintenanceRequest

    reporter = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=5, locale='da_DK')
    description = factory.Faker('paragraph', locale='da_DK')
    location = factory.Faker('word', locale='da_DK')
    priority = 'medium'
    status = 'pending'
    admin_notes = ''


class AuditLogFactory(DjangoModelFactory):
    """Factory for creating AuditLog instances."""

    class Meta:
        model = AuditLog

    user = factory.SubFactory(UserFactory)
    action = 'user_activated'
    target_type = 'User'
    target_id = 1
    details = factory.LazyFunction(lambda: {})
    ip_address = '127.0.0.1'
