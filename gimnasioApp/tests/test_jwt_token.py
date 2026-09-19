"""Tests for SIMPLE_JWT token lifetime configuration.

Extracted from tests.py lines 1263-1297.
"""

from datetime import timedelta
from django.test import TestCase
from django.conf import settings


class TokenLifetimeSettingsTest(TestCase):
    """Tests for SIMPLE_JWT token lifetime configuration."""

    def test_access_token_lifetime_is_15_minutes(self):
        """SIMPLE_JWT ACCESS_TOKEN_LIFETIME should be 15 minutes."""
        self.assertEqual(
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            timedelta(minutes=15)
        )

    def test_refresh_token_lifetime_is_3_days(self):
        """SIMPLE_JWT REFRESH_TOKEN_LIFETIME should be 3 days (72 hours)."""
        self.assertEqual(
            settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
            timedelta(days=3)
        )

    def test_rotate_refresh_tokens_enabled(self):
        """SIMPLE_JWT ROTATE_REFRESH_TOKENS should be True."""
        self.assertTrue(settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS'])

    def test_blacklist_after_rotation_enabled(self):
        """SIMPLE_JWT BLACKLIST_AFTER_ROTATION should be True."""
        self.assertTrue(settings.SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'])