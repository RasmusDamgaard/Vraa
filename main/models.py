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
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
        ]

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
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['message']),
            models.Index(fields=['author']),
        ]

    def __str__(self) -> str:
        preview = self.content[:30]
        if len(self.content) > 30:
            preview += '...'
        return f'{self.author.username}: {preview}'


class Booking(models.Model):
    """A booking for the vacation home."""

    STATUS_CHOICES = [
        ('pending', 'Afventer'),
        ('confirmed', 'Bekræftet'),
        ('cancelled', 'Annulleret'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Bruger',
    )
    start_date = models.DateField(
        verbose_name='Start dato',
    )
    end_date = models.DateField(
        verbose_name='Slut dato',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status',
    )
    notes = models.TextField(
        blank=True,
        max_length=500,
        verbose_name='Noter',
        help_text='Eventuelle bemærkninger til bookingen',
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
        ordering = ['start_date']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookinger'
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user.username}: {self.start_date} - {self.end_date}'

    def clean(self):
        """Validate no overlapping confirmed bookings."""
        from django.core.exceptions import ValidationError

        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError(
                    {'end_date': 'Slut dato skal være efter start dato.'}
                )

            # Check for overlapping confirmed bookings
            overlapping = Booking.objects.filter(
                status='confirmed',
                start_date__lt=self.end_date,
                end_date__gt=self.start_date,
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError('Der er allerede en booking i denne periode.')

    @property
    def duration_days(self) -> int:
        """Return the number of days for this booking."""
        return (self.end_date - self.start_date).days
