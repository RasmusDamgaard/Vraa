"""
Services for sending notifications and emails.
"""
from __future__ import annotations

from django.urls import reverse

from .models import AuditLog, Notification


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
