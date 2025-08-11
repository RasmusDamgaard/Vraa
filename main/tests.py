"""
Tests for the ``main`` application.

This file provides a skeleton for writing unit tests. At present no
tests are implemented, but the structure is ready for future
development.
"""
from __future__ import annotations

from django.test import TestCase  # type: ignore


class SimpleTestCase(TestCase):
    """A simple test case ensuring that pages return an HTTP 200."""

    def test_frontpage(self) -> None:
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
