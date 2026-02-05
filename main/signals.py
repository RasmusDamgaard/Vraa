"""
Signal handlers for the ``main`` application.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Message, UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Message)
def update_message_search_vector(sender, instance, **kwargs):
    """
    Update search vector when a message is saved.
    Uses Danish text search configuration for proper stemming.
    Falls back to simple configuration for SQLite (development).
    """
    # Check if using PostgreSQL (has SearchVector support)
    if connection.vendor == 'postgresql':
        # Update the search vector using a raw update to avoid recursion
        # Using 'danish' config for proper Danish text stemming
        Message.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('content', config='danish')
        )
