#!/usr/bin/env python3
"""
This script serves as the command‑line utility for administrative tasks.

It mirrors the structure of the standard `manage.py` file created by
`django-admin startproject` and delegates to Django’s command line
management functions. To use this script you'll need Django installed in
your environment. See ``requirements.txt`` for installation details.
"""

import os
import sys

def main() -> None:
    """Run administrative tasks."""
    # Set the default settings module for the 'django' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Vraa.settings')
    try:
        from django.core.management import execute_from_command_line  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
