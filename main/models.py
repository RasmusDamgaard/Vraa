"""
Models for the ``main`` application.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import FileExtensionValidator
from django.db import models


class HeritageLine(models.Model):
    """
    Represents one of the 4 family heritage lines.
    Each line has reserved weeks allocated on a rolling basis.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Navn',
        help_text="Navn på familielinjen (f.eks. 'Damgaard-linjen')",
    )
    short_name = models.CharField(
        max_length=20,
        verbose_name='Kort navn',
        help_text="Kort visningsnavn til badges (f.eks. 'Damgaard')",
    )
    description = models.TextField(
        blank=True,
        verbose_name='Beskrivelse',
        help_text='Beskrivelse af denne familielinje',
    )
    color = models.CharField(
        max_length=7,
        default='#2C5F7C',
        verbose_name='Farve',
        help_text="Hex-farvekode til kalenderbegivenheder (f.eks. '#2C5F7C')",
    )
    badge_class = models.CharField(
        max_length=30,
        default='bg-primary',
        verbose_name='Badge klasse',
        help_text="Bootstrap badge klasse (f.eks. 'bg-primary', 'bg-success')",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Rækkefølge',
        help_text='Visningsrækkefølge (lavere tal først)',
    )
    base_weeks = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Baseuger',
        help_text='Basis ugenumre for år 0 rotation (f.eks. [26, 27])',
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
        verbose_name = 'Familielinje'
        verbose_name_plural = 'Familielinjer'
        ordering = ['order', 'name']

    def __str__(self) -> str:
        return self.name

    def get_reserved_weeks_for_year(self, year: int) -> list[int]:
        """
        Calculate reserved weeks for a specific year using rolling rotation.

        The rotation works as follows:
        - Base year (2024) = index 0
        - Each subsequent year, weeks rotate forward by the line's order position

        Example with 4 lines and 2 weeks each:
        - Year 0: Line 1 gets weeks 26-27, Line 2 gets weeks 28-29, etc.
        - Year 1: Line 1 gets weeks 28-29, Line 2 gets weeks 30-31, etc.
        """
        if not self.base_weeks:
            return []

        base_year = 2024  # Reference year for rotation calculation
        year_offset = year - base_year
        total_lines = HeritageLine.objects.count()

        if total_lines == 0:
            return []

        weeks_per_line = len(self.base_weeks)
        start_offset = ((self.order + year_offset) % total_lines) * weeks_per_line

        # Get the actual week numbers
        all_reserved_weeks = list(range(26, 26 + total_lines * weeks_per_line))
        return all_reserved_weeks[start_offset:start_offset + weeks_per_line]


class ReservedWeek(models.Model):
    """
    Represents a reserved week for a heritage line.
    Can be auto-generated based on rotation rules or manually created.
    """

    heritage_line = models.ForeignKey(
        'HeritageLine',
        on_delete=models.CASCADE,
        related_name='reserved_weeks',
        verbose_name='Familielinje',
    )
    year = models.PositiveIntegerField(
        verbose_name='År',
        help_text='Året denne reservation gælder for',
    )
    week_number = models.PositiveSmallIntegerField(
        verbose_name='Ugenummer',
        help_text='ISO ugenummer (1-53)',
    )
    start_date = models.DateField(
        verbose_name='Startdato',
        help_text='Første dag i den reserverede uge (mandag)',
    )
    end_date = models.DateField(
        verbose_name='Slutdato',
        help_text='Sidste dag i den reserverede uge (søndag)',
    )
    is_locked = models.BooleanField(
        default=True,
        verbose_name='Låst',
        help_text='Hvis låst, kan kun medlemmer af denne linje booke i denne uge',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Noter',
        help_text='Admin noter om denne reservation',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_reservations',
        verbose_name='Oprettet af',
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
        verbose_name = 'Reserveret uge'
        verbose_name_plural = 'Reserverede uger'
        ordering = ['year', 'week_number']
        unique_together = ['heritage_line', 'year', 'week_number']
        indexes = [
            models.Index(fields=['year', 'week_number']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self) -> str:
        return f'{self.heritage_line.short_name} - Uge {self.week_number}, {self.year}'

    def save(self, *args, **kwargs):
        """Auto-calculate dates from year and week number."""
        from datetime import datetime, timedelta

        if not self.start_date or not self.end_date:
            # ISO week calculation
            jan4 = datetime(self.year, 1, 4)
            start_of_week1 = jan4 - timedelta(days=jan4.weekday())
            self.start_date = (start_of_week1 + timedelta(weeks=self.week_number - 1)).date()
            self.end_date = self.start_date + timedelta(days=6)
        super().save(*args, **kwargs)

    @classmethod
    def generate_for_year(cls, year: int, created_by=None) -> int:
        """
        Generate all reserved weeks for a given year based on heritage line rotation.
        Returns the number of reserved weeks created.
        """
        created_count = 0

        for line in HeritageLine.objects.all():
            weeks = line.get_reserved_weeks_for_year(year)
            for week_num in weeks:
                _, created = cls.objects.get_or_create(
                    heritage_line=line,
                    year=year,
                    week_number=week_num,
                    defaults={'created_by': created_by},
                )
                if created:
                    created_count += 1

        return created_count

    @classmethod
    def get_reserved_for_date_range(cls, start_date, end_date):
        """Get all reserved weeks overlapping with a date range."""
        return cls.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).select_related('heritage_line')


class UserProfile(models.Model):
    """
    Extended user profile with display name and additional info.
    Created automatically via signal when User is created.
    """

    FAMILY_ROLE_CHOICES = [
        ('member', 'Medlem'),
        ('elder', 'Ældste'),
        ('head', 'Linjehoved'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Bruger',
    )
    display_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Visningsnavn',
        help_text="Navn som vises på beskeder og bookinger (f.eks. 'Rasmus Damgaard')",
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Om mig',
        help_text='Kort beskrivelse (valgfrit)',
    )
    heritage_line = models.ForeignKey(
        'HeritageLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name='Familielinje',
        help_text='Familielinje denne bruger tilhører',
    )
    family_role = models.CharField(
        max_length=20,
        choices=FAMILY_ROLE_CHOICES,
        default='member',
        verbose_name='Familerolle',
        help_text='Rolle i familielinjen',
    )

    # Notification preferences
    NOTIFICATION_PREF_CHOICES = [
        ('all', 'Alle notifikationer'),
        ('mentions_only', 'Kun nævnelser'),
        ('none', 'Ingen e-mailnotifikationer'),
    ]
    email_notification_pref = models.CharField(
        max_length=20,
        choices=NOTIFICATION_PREF_CHOICES,
        default='all',
        verbose_name='E-mailnotifikationer',
        help_text='Hvornår skal du modtage e-mailnotifikationer?',
    )
    notify_new_messages = models.BooleanField(
        default=True,
        verbose_name='Notificer ved nye beskeder',
        help_text='Modtag notifikationer når nye beskeder postes på opslagstavlen',
    )
    notify_comments = models.BooleanField(
        default=True,
        verbose_name='Notificer ved kommentarer',
        help_text='Modtag notifikationer når nogen kommenterer dine beskeder',
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
        verbose_name = 'Brugerprofil'
        verbose_name_plural = 'Brugerprofiler'

    def __str__(self) -> str:
        return f"{self.user.username}'s profil"

    def get_display_name(self) -> str:
        """Return display name if set, otherwise username."""
        return self.display_name if self.display_name else self.user.username

    @property
    def full_display_name(self) -> str:
        """Alias for get_display_name() for template convenience."""
        return self.get_display_name()


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
    search_vector = SearchVectorField(
        null=True,
        blank=True,
        verbose_name='Søgevektor',
        help_text='Automatisk genereret søgevektor til fuldtekstsøgning',
    )

    class Meta:
        ordering = ['-is_pinned', '-pinned_at', '-created_at']
        verbose_name = 'Besked'
        verbose_name_plural = 'Beskeder'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['-is_pinned', '-pinned_at', '-created_at']),
            GinIndex(fields=['search_vector']),
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
        """Validate no overlapping confirmed bookings and check reserved weeks."""
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

            # Check for reserved week conflicts (only if user is set)
            if self.user_id:
                user_line = None
                try:
                    if hasattr(self.user, 'profile') and self.user.profile.heritage_line:
                        user_line = self.user.profile.heritage_line
                except Exception:
                    # Profile might not exist yet
                    pass

                conflicting_reservations = ReservedWeek.get_reserved_for_date_range(
                    self.start_date, self.end_date
                )
                if user_line:
                    conflicting_reservations = conflicting_reservations.exclude(
                        heritage_line=user_line
                    )

                locked_conflicts = conflicting_reservations.filter(is_locked=True)

                if locked_conflicts.exists():
                    conflict = locked_conflicts.first()
                    raise ValidationError({
                        'start_date': (
                            f'Denne periode overlapper med en reserveret uge for '
                            f'{conflict.heritage_line.name} (uge {conflict.week_number}). '
                            f'Kun medlemmer af denne linje kan booke i denne periode.'
                        )
                    })

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
        ('new_message', 'Ny besked på opslagstavlen'),
        ('booking_reminder', 'Påmindelse om kommende booking'),
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
