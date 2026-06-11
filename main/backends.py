"""
Custom authentication backends for the ``main`` application.
"""
from __future__ import annotations

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either a username or an email address.

    If the credential contains '@' it is first looked up as an email.
    Exactly one matching account → authenticate by the resolved username.
    Multiple matching accounts → return None (form handles messaging).
    No matching account → fall through and treat the credential as a
    username (usernames are allowed to contain '@').
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username and '@' in username:
            matches = list(
                User.objects.filter(email__iexact=username).values_list('username', flat=True)
            )
            if len(matches) == 1:
                username = matches[0]
            elif len(matches) > 1:
                return None
        return super().authenticate(request, username=username, password=password, **kwargs)
