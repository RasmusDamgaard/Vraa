"""
Administration configuration for the ``main`` app.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail

from django.utils import timezone

from .models import Booking, Comment, Message, Notification
from .services import NotificationService

logger = logging.getLogger(__name__)

User = get_user_model()


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for managing messages."""

    list_display = ['author', 'content_preview', 'is_pinned', 'created_at']
    list_filter = ['is_pinned', 'created_at', 'author']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'pinned_at', 'pinned_by']
    date_hierarchy = 'created_at'
    actions = ['pin_messages', 'unpin_messages']

    def content_preview(self, obj):
        if len(obj.content) > 75:
            return obj.content[:75] + '...'
        return obj.content
    content_preview.short_description = 'Besked'

    @admin.action(description='Fastgor valgte beskeder')
    def pin_messages(self, request, queryset):
        """Pin selected messages to top of message board."""
        now = timezone.now()
        count = queryset.update(
            is_pinned=True,
            pinned_at=now,
            pinned_by=request.user
        )
        self.message_user(request, f'{count} besked(er) er nu fastgjort.')

    @admin.action(description='Fjern fastgorelse fra valgte beskeder')
    def unpin_messages(self, request, queryset):
        """Unpin selected messages."""
        count = queryset.update(
            is_pinned=False,
            pinned_at=None,
            pinned_by=None
        )
        self.message_user(request, f'{count} besked(er) er ikke laengere fastgjort.')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for managing comments."""

    list_display = ['author', 'message', 'content_preview', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at']
    raw_id_fields = ['message']

    def content_preview(self, obj):
        if len(obj.content) > 50:
            return obj.content[:50] + '...'
        return obj.content
    content_preview.short_description = 'Kommentar'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for managing bookings."""

    list_display = ['user', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    actions = ['approve_bookings', 'reject_bookings']

    def save_model(self, request, obj, form, change):
        """Send notification email and in-app notification when status changes."""
        if change:  # Only for updates, not new objects
            try:
                old_obj = Booking.objects.get(pk=obj.pk)
                status_changed = old_obj.status != obj.status
            except Booking.DoesNotExist:
                status_changed = False
        else:
            status_changed = False

        super().save_model(request, obj, form, change)

        if status_changed:
            # Send email notification
            if obj.user.email:
                self._send_status_notification(obj)
            # Send in-app notification
            self._send_inapp_notification(obj)

    def _send_inapp_notification(self, booking):
        """Send in-app notification about booking status change."""
        if booking.status == 'confirmed':
            NotificationService.notify_booking_approved(booking)
        elif booking.status == 'cancelled':
            NotificationService.notify_booking_rejected(booking)

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
                f'Vi glaeder os til at se dig!\n\n'
                f'Venlig hilsen,\nVraa'
            )
        elif booking.status == 'cancelled':
            subject = 'Din booking er afvist - Vraa'
            message = (
                f'Hej {booking.user.username},\n\n'
                f'Desvaerre er din booking blevet afvist.\n\n'
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
            logger.error(f'Failed to send booking notification: {e}')

    @admin.action(description='Godkend valgte bookinger')
    def approve_bookings(self, request, queryset):
        """Bulk approve bookings and send notifications."""
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'confirmed'
            booking.save()
            if booking.user.email:
                self._send_status_notification(booking)
            self._send_inapp_notification(booking)
            count += 1
        self.message_user(request, f'{count} booking(er) er nu godkendt.')

    @admin.action(description='Afvis valgte bookinger')
    def reject_bookings(self, request, queryset):
        """Bulk reject bookings and send notifications."""
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'cancelled'
            booking.save()
            if booking.user.email:
                self._send_status_notification(booking)
            self._send_inapp_notification(booking)
            count += 1
        self.message_user(request, f'{count} booking(er) er afvist.')


class UserAdmin(BaseUserAdmin):
    """Custom User admin with approval actions."""

    list_display = ['username', 'email', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    actions = ['approve_users', 'deactivate_users']

    @admin.action(description='Godkend valgte brugere')
    def approve_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} bruger(e) er nu godkendt.')

    @admin.action(description='Deaktiver valgte brugere')
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} bruger(e) er nu deaktiveret.')


# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for managing notifications."""

    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='Marker som laest')
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} notifikation(er) markeret som laest.')

    @admin.action(description='Marker som ulaest')
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f'{count} notifikation(er) markeret som ulaest.')
