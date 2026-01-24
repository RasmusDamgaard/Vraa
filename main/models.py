"""
Models for the ``main`` application.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Message(models.Model):
    """A message on the message board."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Forfatter',
    )
    content = models.TextField(
        verbose_name='Besked',
        max_length=2000,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oprettet',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Opdateret',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Besked'
        verbose_name_plural = 'Beskeder'

    def __str__(self) -> str:
        preview = self.content[:50]
        if len(self.content) > 50:
            preview += '...'
        return f'{self.author.username}: {preview}'


class Comment(models.Model):
    """A comment on a message board message."""

    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Besked',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Forfatter',
    )
    content = models.TextField(
        verbose_name='Kommentar',
        max_length=1000,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oprettet',
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Kommentar'
        verbose_name_plural = 'Kommentarer'

    def __str__(self) -> str:
        preview = self.content[:30]
        if len(self.content) > 30:
            preview += '...'
        return f'{self.author.username}: {preview}'
