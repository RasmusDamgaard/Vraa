"""
Services for sending notifications and emails.
"""
from __future__ import annotations

from django.urls import reverse

from .models import Notification


class NotificationService:
    """Service for creating and sending notifications."""

    @staticmethod
    def notify_comment_on_message(message, comment):
        """Notify message author when someone comments."""
        if message.author == comment.author:
            return  # Don't notify self

        content_preview = comment.content[:100]
        if len(comment.content) > 100:
            content_preview += '...'

        Notification.objects.create(
            user=message.author,
            notification_type='comment',
            title='Ny kommentar på din besked',
            message=f'{comment.author.username} kommenterede: "{content_preview}"',
            link=reverse('main:frontpage') + f'#message-{message.pk}',
        )

    @staticmethod
    def notify_booking_approved(booking):
        """Notify user when booking is approved."""
        Notification.objects.create(
            user=booking.user,
            notification_type='booking_approved',
            title='Din booking er godkendt!',
            message=f'Din booking fra {booking.start_date.strftime("%d. %B %Y")} til {booking.end_date.strftime("%d. %B %Y")} er blevet godkendt.',
            link=reverse('main:kalender'),
        )

    @staticmethod
    def notify_booking_rejected(booking):
        """Notify user when booking is rejected."""
        Notification.objects.create(
            user=booking.user,
            notification_type='booking_rejected',
            title='Din booking er afvist',
            message=f'Din booking fra {booking.start_date.strftime("%d. %B %Y")} til {booking.end_date.strftime("%d. %B %Y")} er desværre blevet afvist.',
            link=reverse('main:kalender'),
        )
