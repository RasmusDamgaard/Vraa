"""
Tests for services in the main application.

Tests for NotificationService, AuditService, and WeatherService.
"""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

from main.models import AuditLog, Notification, UserProfile
from main.services import AuditService, NotificationService, WeatherService

from .factories import (
    BookingFactory,
    CommentFactory,
    MessageFactory,
    NotificationFactory,
    UserFactory,
    UserProfileFactory,
)


# =============================================================================
# NotificationService Tests
# =============================================================================


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.mark.django_db
    def test_notify_new_message_creates_notifications(self):
        """notify_new_message creates notifications for subscribed users."""
        author = UserFactory()
        subscriber = UserFactory()

        # Update profile for subscriber with notifications enabled
        subscriber.profile.notify_new_messages = True
        subscriber.profile.email_notification_pref = 'none'  # Disable email for test
        subscriber.profile.save()

        # Update profile for author
        author.profile.notify_new_messages = True
        author.profile.save()

        message = MessageFactory(author=author)

        notifications = NotificationService.notify_new_message(message)

        # Should create notification for subscriber, not for author
        assert len(notifications) == 1
        assert notifications[0].user == subscriber
        assert notifications[0].notification_type == 'new_message'

    @pytest.mark.django_db
    def test_notify_new_message_excludes_author(self):
        """notify_new_message does not notify the message author."""
        author = UserFactory()
        author.profile.notify_new_messages = True
        author.profile.save()

        message = MessageFactory(author=author)

        notifications = NotificationService.notify_new_message(message)

        # Author should not receive notification
        author_notifications = [n for n in notifications if n.user == author]
        assert len(author_notifications) == 0

    @pytest.mark.django_db
    def test_notify_comment_on_message(self):
        """notify_comment_on_message notifies message author."""
        message_author = UserFactory()
        commenter = UserFactory()

        # Update profile for message author
        message_author.profile.notify_comments = True
        message_author.profile.email_notification_pref = 'none'
        message_author.profile.save()

        message = MessageFactory(author=message_author)
        comment = CommentFactory(message=message, author=commenter)

        notification = NotificationService.notify_comment_on_message(message, comment)

        assert notification is not None
        assert notification.user == message_author
        assert notification.notification_type == 'comment'

    @pytest.mark.django_db
    def test_notify_comment_on_own_message_returns_none(self):
        """notify_comment_on_message returns None when commenting on own message."""
        user = UserFactory()

        message = MessageFactory(author=user)
        comment = CommentFactory(message=message, author=user)

        notification = NotificationService.notify_comment_on_message(message, comment)

        assert notification is None

    @pytest.mark.django_db
    def test_notify_mention(self):
        """notify_mention creates notification for mentioned user."""
        author = UserFactory()
        mentioned_user = UserFactory()
        mentioned_user.profile.email_notification_pref = 'none'
        mentioned_user.profile.save()

        message = MessageFactory(author=author)

        notification = NotificationService.notify_mention(
            mentioned_user, message, author
        )

        assert notification is not None
        assert notification.user == mentioned_user
        assert notification.notification_type == 'mention'

    @pytest.mark.django_db
    def test_notify_mention_self_returns_none(self):
        """notify_mention returns None when mentioning self."""
        user = UserFactory()
        message = MessageFactory(author=user)

        notification = NotificationService.notify_mention(user, message, user)

        assert notification is None

    @pytest.mark.django_db
    def test_parse_and_notify_mentions_finds_users(self):
        """parse_and_notify_mentions finds @mentioned users."""
        author = UserFactory()
        mentioned_user = UserFactory(username='rasmus')
        mentioned_user.profile.email_notification_pref = 'none'
        mentioned_user.profile.save()

        message = MessageFactory(author=author, content='Hey @rasmus, check this out!')

        mentioned = NotificationService.parse_and_notify_mentions(
            message.content, author, message
        )

        assert mentioned_user in mentioned
        assert Notification.objects.filter(
            user=mentioned_user,
            notification_type='mention',
        ).exists()

    @pytest.mark.django_db
    def test_parse_and_notify_mentions_ignores_nonexistent_users(self):
        """parse_and_notify_mentions ignores mentions of nonexistent users."""
        author = UserFactory()
        message = MessageFactory(author=author, content='Hey @nonexistent, hello!')

        mentioned = NotificationService.parse_and_notify_mentions(
            message.content, author, message
        )

        assert len(mentioned) == 0

    @pytest.mark.django_db
    def test_notify_booking_approved(self):
        """notify_booking_approved creates notification."""
        user = UserFactory()
        user.profile.email_notification_pref = 'none'
        user.profile.save()

        booking = BookingFactory(user=user, status='confirmed')

        notification = NotificationService.notify_booking_approved(booking)

        assert notification is not None
        assert notification.user == user
        assert notification.notification_type == 'booking_approved'

    @pytest.mark.django_db
    def test_notify_booking_rejected(self):
        """notify_booking_rejected creates notification."""
        user = UserFactory()
        user.profile.email_notification_pref = 'none'
        user.profile.save()

        booking = BookingFactory(user=user, status='cancelled')

        notification = NotificationService.notify_booking_rejected(booking)

        assert notification is not None
        assert notification.user == user
        assert notification.notification_type == 'booking_rejected'

    @pytest.mark.django_db
    @patch('main.services.send_mail')
    def test_send_notification_email(self, mock_send_mail):
        """send_notification_email sends email to user."""
        user = UserFactory(email='test@example.com')
        notification = NotificationFactory(
            user=user,
            title='Test Title',
            message='Test message',
        )

        result = NotificationService.send_notification_email(notification)

        assert result is True
        mock_send_mail.assert_called_once()

    @pytest.mark.django_db
    def test_send_notification_email_no_email(self):
        """send_notification_email returns False when user has no email."""
        user = UserFactory(email='')
        notification = NotificationFactory(user=user)

        result = NotificationService.send_notification_email(notification)

        assert result is False


# =============================================================================
# AuditService Tests
# =============================================================================


class TestAuditService:
    """Tests for AuditService."""

    @pytest.mark.django_db
    def test_get_client_ip_direct(self):
        """get_client_ip returns REMOTE_ADDR when no proxy."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        ip = AuditService.get_client_ip(request)

        assert ip == '192.168.1.1'

    @pytest.mark.django_db
    def test_get_client_ip_forwarded(self):
        """get_client_ip returns first X-Forwarded-For IP."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 10.0.0.2'
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        ip = AuditService.get_client_ip(request)

        assert ip == '10.0.0.1'

    @pytest.mark.django_db
    def test_log_creates_audit_entry(self):
        """log creates an audit log entry."""
        user = UserFactory()
        target = UserFactory()

        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        AuditService.log(
            request,
            'user_activated',
            target,
            {'username': target.username},
        )

        log = AuditLog.objects.latest('created_at')
        assert log.user == user
        assert log.action == 'user_activated'
        assert log.target_type == 'User'
        assert log.target_id == target.pk
        assert log.details['username'] == target.username

    @pytest.mark.django_db
    def test_log_user_activated(self):
        """log_user_activated creates correct log entry."""
        admin = UserFactory(is_staff=True)
        user = UserFactory(username='newuser', email='new@example.com')

        factory = RequestFactory()
        request = factory.get('/')
        request.user = admin
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        AuditService.log_user_activated(request, user)

        log = AuditLog.objects.latest('created_at')
        assert log.action == 'user_activated'
        assert log.details['username'] == 'newuser'
        assert log.details['email'] == 'new@example.com'

    @pytest.mark.django_db
    def test_log_user_deactivated(self):
        """log_user_deactivated creates correct log entry."""
        admin = UserFactory(is_staff=True)
        user = UserFactory(username='olduser')

        factory = RequestFactory()
        request = factory.get('/')
        request.user = admin
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        AuditService.log_user_deactivated(request, user)

        log = AuditLog.objects.latest('created_at')
        assert log.action == 'user_deactivated'
        assert log.details['username'] == 'olduser'

    @pytest.mark.django_db
    def test_log_booking_approved(self):
        """log_booking_approved creates correct log entry."""
        admin = UserFactory(is_staff=True)
        booking = BookingFactory()

        factory = RequestFactory()
        request = factory.get('/')
        request.user = admin
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        AuditService.log_booking_approved(request, booking)

        log = AuditLog.objects.latest('created_at')
        assert log.action == 'booking_approved'
        assert 'start_date' in log.details
        assert 'end_date' in log.details

    @pytest.mark.django_db
    def test_log_booking_rejected(self):
        """log_booking_rejected creates correct log entry."""
        admin = UserFactory(is_staff=True)
        booking = BookingFactory()

        factory = RequestFactory()
        request = factory.get('/')
        request.user = admin
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        AuditService.log_booking_rejected(request, booking)

        log = AuditLog.objects.latest('created_at')
        assert log.action == 'booking_rejected'


# =============================================================================
# WeatherService Tests
# =============================================================================


class TestWeatherService:
    """Tests for WeatherService."""

    def test_get_base_symbol_removes_day_suffix(self):
        """get_base_symbol removes _day suffix."""
        result = WeatherService.get_base_symbol('clearsky_day')
        assert result == 'clearsky'

    def test_get_base_symbol_removes_night_suffix(self):
        """get_base_symbol removes _night suffix."""
        result = WeatherService.get_base_symbol('clearsky_night')
        assert result == 'clearsky'

    def test_get_base_symbol_no_suffix(self):
        """get_base_symbol returns symbol unchanged if no suffix."""
        result = WeatherService.get_base_symbol('rain')
        assert result == 'rain'

    def test_get_base_symbol_none(self):
        """get_base_symbol handles None input."""
        result = WeatherService.get_base_symbol(None)
        assert result is None

    def test_get_weather_emoji_clearsky(self):
        """get_weather_emoji returns sun emoji for clearsky."""
        emoji = WeatherService.get_weather_emoji('clearsky_day')
        assert emoji == '☀️'

    def test_get_weather_emoji_rain(self):
        """get_weather_emoji returns rain emoji for rain."""
        emoji = WeatherService.get_weather_emoji('rain')
        assert emoji == '🌧️'

    def test_get_weather_emoji_unknown(self):
        """get_weather_emoji returns thermometer for unknown symbol."""
        emoji = WeatherService.get_weather_emoji('unknownsymbol')
        assert emoji == '🌡️'

    @pytest.mark.django_db
    @patch('main.services.requests.get')
    @patch('main.services.cache')
    def test_get_weather_success(self, mock_cache, mock_get):
        """get_weather returns weather data on success."""
        mock_cache.get.return_value = None  # No cached data

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            'properties': {
                'timeseries': [{
                    'time': '2024-07-01T12:00:00Z',
                    'data': {
                        'instant': {
                            'details': {
                                'air_temperature': 22.5,
                                'wind_speed': 5.2,
                                'relative_humidity': 65,
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
        assert weather['temperature'] == 22  # Rounded (22.5 -> 22 via banker's rounding)
        assert weather['emoji'] == '☀️'
        assert weather['location'] == 'Anholt'

    @pytest.mark.django_db
    @patch('main.services.requests.get')
    @patch('main.services.cache')
    def test_get_weather_returns_cached_data(self, mock_cache, mock_get):
        """get_weather returns cached data if available."""
        cached_weather = {
            'temperature': 20,
            'emoji': '☀️',
            'location': 'Anholt',
        }
        mock_cache.get.return_value = cached_weather

        weather = WeatherService.get_weather()

        assert weather == cached_weather
        mock_get.assert_not_called()  # Should not make API call

    @pytest.mark.django_db
    @patch('main.services.requests.get')
    @patch('main.services.cache')
    def test_get_weather_handles_api_error(self, mock_cache, mock_get):
        """get_weather returns None on API error."""
        import requests
        mock_cache.get.return_value = None
        mock_get.side_effect = requests.exceptions.RequestException('Network error')

        weather = WeatherService.get_weather()

        assert weather is None

    @pytest.mark.django_db
    @patch('main.services.requests.get')
    @patch('main.services.cache')
    def test_get_weather_handles_empty_response(self, mock_cache, mock_get):
        """get_weather returns None when no timeseries data."""
        mock_cache.get.return_value = None

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            'properties': {
                'timeseries': []
            }
        }
        mock_get.return_value = mock_response

        weather = WeatherService.get_weather()

        assert weather is None
