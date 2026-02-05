"""
Pytest configuration and shared fixtures for the Vraa project.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a regular test user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        is_active=True,
    )
    return user


@pytest.fixture
def other_user(db):
    """Create another regular test user."""
    user = User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpass123',
        is_active=True,
    )
    return user


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    user = User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        is_staff=True,
        is_active=True,
    )
    return user


@pytest.fixture
def admin_user(db):
    """Create a superuser."""
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
    )
    return user


@pytest.fixture
def authenticated_client(client, user):
    """Return a client logged in as regular user."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def other_authenticated_client(client, other_user):
    """Return a client logged in as another user."""
    from django.test import Client
    other_client = Client()
    other_client.login(username='otheruser', password='testpass123')
    return other_client


@pytest.fixture
def staff_client(client, staff_user):
    """Return a client logged in as staff."""
    client.login(username='staffuser', password='testpass123')
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return a client logged in as admin."""
    client.login(username='admin', password='adminpass123')
    return client


@pytest.fixture
def future_date():
    """Factory for creating future dates."""
    def _future_date(days: int = 5) -> date:
        return date.today() + timedelta(days=days)
    return _future_date


@pytest.fixture
def past_date():
    """Factory for creating past dates."""
    def _past_date(days: int = 5) -> date:
        return date.today() - timedelta(days=days)
    return _past_date
