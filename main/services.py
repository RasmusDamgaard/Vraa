"""
Services for sending notifications, emails, and external API integrations.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from .models import AuditLog, Notification, UserProfile

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and sending notifications."""

    @staticmethod
    def get_site_url():
        """Get the site URL for email links."""
        return getattr(settings, 'SITE_URL', 'https://vraa.org')

    @staticmethod
    def notify_new_message(message):
        """
        Notify users who have opted in to new message notifications.
        Excludes the message author.
        """
        # Get users who want new message notifications
        profiles = UserProfile.objects.filter(
            notify_new_messages=True,
        ).exclude(user=message.author).select_related('user')

        # Get author display name
        if hasattr(message.author, 'profile'):
            author_name = message.author.profile.get_display_name()
        else:
            author_name = message.author.username

        content_preview = message.content[:50]
        if len(message.content) > 50:
            content_preview += '...'

        notifications_created = []
        for profile in profiles:
            notification = Notification.objects.create(
                user=profile.user,
                notification_type='new_message',
                title='Ny besked på opslagstavlen',
                message=f'{author_name} har skrevet en ny besked: "{content_preview}"',
                link=reverse('main:frontpage') + f'#message-{message.pk}',
            )
            notifications_created.append(notification)

            # Send email if user wants it
            if profile.email_notification_pref == 'all':
                NotificationService.send_notification_email(notification)

        return notifications_created

    @staticmethod
    def notify_comment_on_message(message, comment):
        """
        Enhanced: Notify message author when someone comments.
        Respects user notification preferences.
        """
        # Skip if commenting on own message
        if message.author == comment.author:
            return None

        # Get author display name
        if hasattr(comment.author, 'profile'):
            author_name = comment.author.profile.get_display_name()
        else:
            author_name = comment.author.username

        content_preview = comment.content[:100]
        if len(comment.content) > 100:
            content_preview += '...'

        notification = Notification.objects.create(
            user=message.author,
            notification_type='comment',
            title='Ny kommentar på din besked',
            message=f'{author_name} kommenterede: "{content_preview}"',
            link=reverse('main:frontpage') + f'#message-{message.pk}',
        )

        # Send email if user profile allows
        if hasattr(message.author, 'profile'):
            profile = message.author.profile
            if profile.email_notification_pref in ('all', 'mentions_only') and profile.notify_comments:
                NotificationService.send_notification_email(notification)

        return notification

    @staticmethod
    def notify_mention(mentioned_user, source_object, author):
        """Notify a user when they are mentioned with @username."""
        if mentioned_user == author:
            return None

        # Get author display name
        if hasattr(author, 'profile'):
            author_name = author.profile.get_display_name()
        else:
            author_name = author.username

        content_preview = source_object.content[:50]
        if len(source_object.content) > 50:
            content_preview += '...'

        # Determine link based on object type
        if hasattr(source_object, 'message'):
            # It's a comment
            link = reverse('main:frontpage') + f'#message-{source_object.message.pk}'
        else:
            # It's a message
            link = reverse('main:frontpage') + f'#message-{source_object.pk}'

        notification = Notification.objects.create(
            user=mentioned_user,
            notification_type='mention',
            title='Du blev nævnt i en besked',
            message=f'{author_name} nævnte dig: "{content_preview}"',
            link=link,
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
        if not notification.user.email:
            return False

        site_url = NotificationService.get_site_url()

        try:
            html_message = render_to_string('main/email/notification.html', {
                'notification': notification,
                'site_url': site_url,
            })
        except Exception as e:
            logger.error(f'Failed to render notification email template: {e}')
            html_message = None

        plain_message = f"{notification.message}\n\nSe mere: {site_url}{notification.link}"

        try:
            send_mail(
                subject=notification.title,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[notification.user.email],
                html_message=html_message,
                fail_silently=True,
            )
            logger.info(f'Notification email sent to {notification.user.email}')
            return True
        except Exception as e:
            logger.error(f'Failed to send notification email: {e}')
            return False

    @staticmethod
    def notify_booking_approved(booking):
        """Notify user when booking is approved."""
        notification = Notification.objects.create(
            user=booking.user,
            notification_type='booking_approved',
            title='Din booking er godkendt!',
            message=f'Din booking fra {booking.start_date.strftime("%d. %B %Y")} til {booking.end_date.strftime("%d. %B %Y")} er blevet godkendt.',
            link=reverse('main:kalender'),
        )

        # Send email notification
        if hasattr(booking.user, 'profile') and booking.user.profile.email_notification_pref != 'none':
            NotificationService.send_notification_email(notification)

        return notification

    @staticmethod
    def notify_booking_rejected(booking, reason=''):
        """Notify user when booking is rejected."""
        message = f'Din booking fra {booking.start_date.strftime("%d. %B %Y")} til {booking.end_date.strftime("%d. %B %Y")} er desværre blevet afvist.'
        if reason:
            message += f' Begrundelse: {reason}'
        notification = Notification.objects.create(
            user=booking.user,
            notification_type='booking_rejected',
            title='Din booking er afvist',
            message=message,
            link=reverse('main:kalender'),
        )

        # Send email notification
        if hasattr(booking.user, 'profile') and booking.user.profile.email_notification_pref != 'none':
            NotificationService.send_notification_email(notification)

        return notification


class AuditService:
    """Service for logging audit events."""

    @staticmethod
    def get_client_ip(request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def log(request, action, target, details=None):
        """Create an audit log entry."""
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            target_type=target.__class__.__name__,
            target_id=target.pk,
            details=details or {},
            ip_address=AuditService.get_client_ip(request),
        )

    @staticmethod
    def log_user_activated(request, user):
        """Log when a user is activated."""
        AuditService.log(
            request,
            'user_activated',
            user,
            {'username': user.username, 'email': user.email},
        )

    @staticmethod
    def log_user_deactivated(request, user):
        """Log when a user is deactivated."""
        AuditService.log(
            request,
            'user_deactivated',
            user,
            {'username': user.username, 'email': user.email},
        )

    @staticmethod
    def log_booking_approved(request, booking):
        """Log when a booking is approved."""
        AuditService.log(
            request,
            'booking_approved',
            booking,
            {
                'user': booking.user.username,
                'start_date': str(booking.start_date),
                'end_date': str(booking.end_date),
            },
        )

    @staticmethod
    def log_booking_rejected(request, booking):
        """Log when a booking is rejected."""
        AuditService.log(
            request,
            'booking_rejected',
            booking,
            {
                'user': booking.user.username,
                'start_date': str(booking.start_date),
                'end_date': str(booking.end_date),
            },
        )

    @staticmethod
    def log_document_uploaded(request, document):
        """Log when a document is uploaded."""
        AuditService.log(
            request,
            'document_uploaded',
            document,
            {
                'title': document.title,
                'category': document.category,
                'document_date': str(document.document_date),
            },
        )

    @staticmethod
    def log_document_deleted(request, document):
        """Log when a document is deleted."""
        AuditService.log(
            request,
            'document_deleted',
            document,
            {
                'title': document.title,
                'category': document.category,
            },
        )


class WeatherService:
    """Service for fetching weather data from yr.no (MET Norway API)."""

    # Anholt coordinates (Vraa is on Anholt island)
    LAT = 56.7167
    LON = 11.5167
    LOCATION_NAME = 'Anholt'

    CACHE_KEY = 'vraa_weather'
    CACHE_TIMEOUT = 3600  # 1 hour

    # Weather symbol codes to emoji mapping
    WEATHER_SYMBOLS = {
        'clearsky': '☀️',
        'fair': '🌤️',
        'partlycloudy': '⛅',
        'cloudy': '☁️',
        'fog': '🌫️',
        'lightrainshowers': '🌦️',
        'rainshowers': '🌧️',
        'heavyrainshowers': '🌧️',
        'lightrain': '🌧️',
        'rain': '🌧️',
        'heavyrain': '🌧️',
        'lightsleet': '🌨️',
        'sleet': '🌨️',
        'heavysleet': '🌨️',
        'lightsnow': '🌨️',
        'snow': '❄️',
        'heavysnow': '❄️',
        'lightsleetshowers': '🌨️',
        'sleetshowers': '🌨️',
        'heavysleetshowers': '🌨️',
        'lightsnowshowers': '🌨️',
        'snowshowers': '❄️',
        'heavysnowshowers': '❄️',
        'thunder': '⛈️',
        'thundershowers': '⛈️',
    }

    # Day/night variants map to base symbol
    DAY_NIGHT_SUFFIXES = ['_day', '_night', '_polartwilight']

    @classmethod
    def get_base_symbol(cls, symbol_code):
        """Extract base symbol from symbol code (remove day/night suffix)."""
        if not symbol_code:
            return None
        for suffix in cls.DAY_NIGHT_SUFFIXES:
            if symbol_code.endswith(suffix):
                return symbol_code[:-len(suffix)]
        return symbol_code

    @classmethod
    def get_weather_emoji(cls, symbol_code):
        """Get emoji for a weather symbol code."""
        base_symbol = cls.get_base_symbol(symbol_code)
        return cls.WEATHER_SYMBOLS.get(base_symbol, '🌡️')

    @classmethod
    def get_weather(cls):
        """
        Fetch current weather and forecast from yr.no API.
        Returns cached data if available, otherwise fetches fresh data.

        Returns:
            dict or None: Weather data or None if fetch failed
        """
        # Check cache first
        cached_data = cache.get(cls.CACHE_KEY)
        if cached_data:
            return cached_data

        try:
            url = (
                f'https://api.met.no/weatherapi/locationforecast/2.0/compact'
                f'?lat={cls.LAT}&lon={cls.LON}'
            )
            headers = {
                'User-Agent': 'VraaVacationHome/1.0 (https://vraa.org)',
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            timeseries = data.get('properties', {}).get('timeseries', [])

            if not timeseries:
                logger.warning('No timeseries data in weather response')
                return None

            # Current weather (first entry)
            current_entry = timeseries[0]
            current_instant = current_entry.get('data', {}).get('instant', {}).get('details', {})
            current_next = current_entry.get('data', {}).get('next_1_hours', {})
            symbol_code = current_next.get('summary', {}).get('symbol_code', '')

            weather = {
                'location': cls.LOCATION_NAME,
                'temperature': round(current_instant.get('air_temperature', 0)),
                'wind_speed': round(current_instant.get('wind_speed', 0)),
                'humidity': round(current_instant.get('relative_humidity', 0)),
                'symbol_code': symbol_code,
                'emoji': cls.get_weather_emoji(symbol_code),
                'updated': current_entry.get('time', ''),
                'forecast': [],
            }

            # 3-day forecast (take readings at noon each day)
            forecast_hours = [24, 48, 72]  # Hours from now
            for i, hours in enumerate(forecast_hours):
                if hours < len(timeseries):
                    entry = timeseries[min(hours, len(timeseries) - 1)]
                    instant = entry.get('data', {}).get('instant', {}).get('details', {})
                    next_hours = entry.get('data', {}).get('next_6_hours', {}) or entry.get('data', {}).get('next_1_hours', {})
                    forecast_symbol = next_hours.get('summary', {}).get('symbol_code', '')

                    # Parse the time to get the day name
                    entry_time = entry.get('time', '')
                    try:
                        dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                        day_names = ['Man', 'Tir', 'Ons', 'Tor', 'Fre', 'Lør', 'Søn']
                        day_name = day_names[dt.weekday()]
                    except (ValueError, IndexError):
                        day_name = f'Dag {i + 1}'

                    weather['forecast'].append({
                        'day': day_name,
                        'temp': round(instant.get('air_temperature', 0)),
                        'emoji': cls.get_weather_emoji(forecast_symbol),
                    })

            # Cache the result
            cache.set(cls.CACHE_KEY, weather, cls.CACHE_TIMEOUT)
            return weather

        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to fetch weather data: {e}')
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f'Error parsing weather data: {e}')
            return None
