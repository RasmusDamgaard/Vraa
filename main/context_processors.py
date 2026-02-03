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
