"""
Tests for the ``main`` application.

This module contains basic test cases verifying that the application is
reachable and renders expected content. At least one test is implemented
to ensure the testing infrastructure remains functional.
"""
from __future__ import annotations

from django.test import TestCase  # type: ignore
from django.urls import reverse


class SimpleTestCase(TestCase):
    """A simple test case ensuring that pages return an HTTP 200."""

    def test_frontpage(self) -> None:
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_bootstrap_integrity_hash(self) -> None:
        """The base template should include the correct SRI hash for Bootstrap."""
        response = self.client.get('/')
        self.assertContains(
            response,
            'integrity="sha384-OLBgp1GsljhM2TJ+sbHjaiH9txEUvgdDTAzHv2P24donTt6/529l+9Ua0vFImLlb"',
        )

    def test_information_page(self) -> None:
        response = self.client.get(reverse('main:information'))
        self.assertEqual(response.status_code, 200)

    def test_referater_page(self) -> None:
        response = self.client.get(reverse('main:referater'))
        self.assertEqual(response.status_code, 200)

    def test_vedtaegter_page(self) -> None:
        response = self.client.get(reverse('main:vedtaegter'))
        self.assertEqual(response.status_code, 200)

    def test_kalender_page(self) -> None:
        response = self.client.get(reverse('main:kalender'))
        self.assertEqual(response.status_code, 200)
