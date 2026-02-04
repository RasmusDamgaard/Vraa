"""
Models for the ``main`` application.
"""
from __future__ import annotations

from django.conf import settings
from django.core.validators import FileExtensionValidator
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
    is_pinned = models.BooleanField(
        default=False,
        verbose_name='Fastgjort',
        help_text='Fastgjorte beskeder vises øverst på opslagstavlen',
    )
    pinned_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fastgjort tidspunkt',
    )
    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pinned_messages',
        verbose_name='Fastgjort af',
    )

    class Meta:
        ordering = ['-is_pinned', '-pinned_at', '-created_at']
        verbose_name = 'Besked'
        verbose_name_plural = 'Beskeder'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['-is_pinned', '-pinned_at', '-created_at']),
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


class Notification(models.Model):
    """User notification for various events."""

    NOTIFICATION_TYPES = [
        ('comment', 'Ny kommentar'),
        ('booking_approved', 'Booking godkendt'),
        ('booking_rejected', 'Booking afvist'),
        ('mention', 'Du blev nævnt'),
        ('reply', 'Svar på din kommentar'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Bruger',
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Type',
    )
    title = models.CharField(
        max_length=100,
        verbose_name='Titel',
    )
    message = models.TextField(
        max_length=500,
        verbose_name='Besked',
    )
    link = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Link',
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Læst',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oprettet',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notifikation'
        verbose_name_plural = 'Notifikationer'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self) -> str:
        return f'{self.user.username}: {self.title}'


def document_upload_path(instance, filename):
    """Generate upload path based on category and year."""
    year = instance.document_date.year if instance.document_date else 'other'
    return f'documents/{instance.category}/{year}/{filename}'


class Document(models.Model):
    """A document (referat, vedtaegt, etc.)"""

    CATEGORY_CHOICES = [
        ('referat', 'Referat'),
        ('vedtaegt', 'Vedtægt'),
        ('other', 'Andet'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name='Titel',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Kategori',
    )
    file = models.FileField(
        upload_to=document_upload_path,
        verbose_name='Fil',
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])],
    )
    document_date = models.DateField(
        verbose_name='Dokument dato',
        help_text='Datoen for dokumentet (f.eks. dato for generalforsamling)',
    )
    description = models.TextField(
        blank=True,
        max_length=500,
        verbose_name='Beskrivelse',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name='Uploadet af',
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Uploadet',
    )

    class Meta:
        ordering = ['-document_date']
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumenter'
        indexes = [
            models.Index(fields=['category', '-document_date']),
        ]

    def __str__(self) -> str:
        return f'{self.get_category_display()}: {self.title}'


class MaintenanceRequest(models.Model):
    """A maintenance request for reporting issues at the vacation home."""

    STATUS_CHOICES = [
        ('pending', 'Afventer'),
        ('in_progress', 'Under behandling'),
        ('resolved', 'Løst'),
        ('wont_fix', 'Afvist'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Lav'),
        ('medium', 'Normal'),
        ('high', 'Høj'),
        ('urgent', 'Akut'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        verbose_name='Indberetter',
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Titel',
    )
    description = models.TextField(
        max_length=2000,
        verbose_name='Beskrivelse',
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Placering',
        help_text='Hvor på ejendommen er problemet?',
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Prioritet',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status',
    )
    admin_notes = models.TextField(
        blank=True,
        max_length=1000,
        verbose_name='Admin noter',
        help_text='Interne noter fra administrator',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oprettet',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Opdateret',
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Løst',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vedligeholdelsesanmodning'
        verbose_name_plural = 'Vedligeholdelsesanmodninger'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['reporter']),
            models.Index(fields=['priority']),
        ]

    def __str__(self) -> str:
        return f'{self.title} ({self.get_status_display()})'


class AuditLog(models.Model):
    """Log of important actions for accountability."""

    ACTION_CHOICES = [
        ('booking_approved', 'Booking godkendt'),
        ('booking_rejected', 'Booking afvist'),
        ('user_activated', 'Bruger aktiveret'),
        ('user_deactivated', 'Bruger deaktiveret'),
        ('message_deleted', 'Besked slettet'),
        ('document_uploaded', 'Dokument uploadet'),
        ('document_deleted', 'Dokument slettet'),
        ('maintenance_created', 'Vedligeholdelsesanmodning oprettet'),
        ('maintenance_updated', 'Vedligeholdelsesanmodning opdateret'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='Bruger',
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='Handling',
    )
    target_type = models.CharField(
        max_length=50,
        verbose_name='Måltype',
        help_text='Model name of the affected object',
    )
    target_id = models.PositiveIntegerField(
        verbose_name='Mål-ID',
        help_text='Primary key of the affected object',
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Detaljer',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP-adresse',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Tidspunkt',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Aktivitetslog'
        verbose_name_plural = 'Aktivitetslogs'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]

    def __str__(self) -> str:
        return f'{self.user}: {self.get_action_display()} ({self.created_at})'
