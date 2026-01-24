"""
Administration configuration for the ``main`` app.
"""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Comment, Message

User = get_user_model()


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for managing messages."""

    list_display = ['author', 'content_preview', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        if len(obj.content) > 75:
            return obj.content[:75] + '...'
        return obj.content
    content_preview.short_description = 'Besked'


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
