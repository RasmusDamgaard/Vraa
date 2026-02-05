"""
Middleware for site-wide authentication requirements and security headers.
"""
from __future__ import annotations

from django.shortcuts import redirect
from django.urls import reverse


class PermissionsPolicyMiddleware:
    """
    Middleware to add Permissions-Policy header for enhanced security.
    Restricts access to browser features that are not needed by this application.
    This helps prevent malicious scripts from accessing sensitive device features.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Disable browser features not needed by this application
        # This prevents potential abuse by scripts or embedded content
        response['Permissions-Policy'] = (
            'accelerometer=(), '
            'ambient-light-sensor=(), '
            'autoplay=(), '
            'battery=(), '
            'camera=(), '
            'cross-origin-isolated=(), '
            'display-capture=(), '
            'document-domain=(), '
            'encrypted-media=(), '
            'execution-while-not-rendered=(), '
            'execution-while-out-of-viewport=(), '
            'fullscreen=(), '
            'geolocation=(), '
            'gyroscope=(), '
            'keyboard-map=(), '
            'magnetometer=(), '
            'microphone=(), '
            'midi=(), '
            'navigation-override=(), '
            'payment=(), '
            'picture-in-picture=(), '
            'publickey-credentials-get=(), '
            'screen-wake-lock=(), '
            'sync-xhr=(), '
            'usb=(), '
            'web-share=(), '
            'xr-spatial-tracking=()'
        )
        return response


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
        '/health/',  # Health check endpoint for monitoring
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
