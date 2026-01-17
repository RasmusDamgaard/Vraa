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
