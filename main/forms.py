"""
Forms for the ``main`` application.
"""
from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from .models import Booking


class BookingForm(forms.ModelForm):
    """Form for creating and editing bookings."""

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'end_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError(
                    {'end_date': 'Slut dato skal være efter start dato.'}
                )

            # Check for overlapping confirmed bookings
            overlapping = Booking.objects.filter(
                status='confirmed',
                start_date__lt=end_date,
                end_date__gt=start_date,
            )

            # Exclude current instance if editing
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise ValidationError(
                    'Der er allerede en booking i denne periode.'
                )

        return cleaned_data
