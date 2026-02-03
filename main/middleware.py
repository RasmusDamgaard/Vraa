"""
Middleware for site-wide authentication requirements.
"""
from __future__ import annotations

from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """
    Middleware that requires authentication for all views except
    explicitly exempted URLs.
    """

    EXEMPT_URLS = [
        '/login/',
        '/register/',
        '/brugervejledning/',  # Keep user guide public
        '/admin/',  # Django admin has its own auth
        '/password-reset/',  # Password reset flow must be accessible
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info

            # Check if path is exempt
            is_exempt = any(
                path.startswith(exempt_url)
                for exempt_url in self.EXEMPT_URLS
            )

            # Also exempt static files
            if path.startswith('/static/'):
                is_exempt = True

            if not is_exempt:
                return redirect(f"{reverse('main:login')}?next={path}")

        return self.get_response(request)
