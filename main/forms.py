"""
Forms for the ``main`` application.
"""
from __future__ import annotations

import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import Booking


class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with email field and whitespace-friendly username."""

    email = forms.EmailField(
        required=True,
        label='E-mail',
        help_text='Indtast din e-mailadresse. Denne bruges til at kontakte dig.',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    # Custom username validator that allows whitespace
    username_validator = RegexValidator(
        regex=r'^[\w\s.@+-]+$',
        message='Brugernavn må kun indeholde bogstaver, tal, mellemrum og @/./+/-/_.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override the default username field with our custom validator
        self.fields['username'].validators = [self.username_validator]
        self.fields['username'].help_text = 'Brugernavn må indeholde bogstaver, tal, mellemrum og @/./+/-/_.'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username already exists (case-insensitive)
            if User.objects.filter(username__iexact=username).exists():
                raise ValidationError('Dette brugernavn er allerede i brug.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError('Denne e-mail er allerede registreret.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


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
