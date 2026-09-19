"""Tests for CSRF cookie settings and helper functions.

Extracted from tests.py lines 1299-1395.
"""

from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from django.http import HttpResponse


class CSRFSettingTest(TestCase):
    """Tests for CSRF_ENFORCE feature flag."""

    def test_csrf_enforce_is_enabled(self):
        """CSRF_ENFORCE should be True (enforce mode enabled)."""
        from django.conf import settings

        self.assertTrue(settings.CSRF_ENFORCE)


class CSRFCookieHelperTest(TestCase):
    """Tests for CSRF cookie helper functions in auth_cookie.py."""

    def setUp(self):
        self.response = HttpResponse()

    def test_set_csrf_cookie_sets_correct_attributes_in_development(self):
        """set_csrf_cookie should set cookie with HttpOnly=False, SameSite=Lax, correct path in DEBUG=True."""
        from gimnasioApp.auth_cookie import set_csrf_cookie

        with override_settings(DEBUG=True):
            set_csrf_cookie(self.response, 'test-csrf-token')

            cookie = self.response.cookies.get('csrftoken')
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, 'test-csrf-token')
            self.assertFalse(cookie['httponly'])  # HttpOnly=False for JS access
            self.assertEqual(cookie['samesite'], 'Lax')  # SameSite=Lax in dev
            self.assertEqual(cookie['path'], '/')  # Root path for JS access from any frontend route
            self.assertEqual(cookie['max-age'], 86400)  # 1 day
            self.assertFalse(cookie['secure'])  # Not secure in dev

    def test_set_csrf_cookie_sets_correct_attributes_in_production(self):
        """set_csrf_cookie should set cookie with Secure=True, SameSite=None in DEBUG=False."""
        from gimnasioApp.auth_cookie import set_csrf_cookie

        with override_settings(DEBUG=False):
            set_csrf_cookie(self.response, 'prod-csrf-token')

            cookie = self.response.cookies.get('csrftoken')
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, 'prod-csrf-token')
            self.assertFalse(cookie['httponly'])  # HttpOnly=False for JS access
            self.assertEqual(cookie['samesite'], 'None')  # SameSite=None in prod
            self.assertEqual(cookie['path'], '/')  # Root path for JS access from any frontend route
            self.assertEqual(cookie['max-age'], 86400)  # 1 day
            self.assertTrue(cookie['secure'])  # Secure in prod

    def test_clear_csrf_cookie_clears_with_correct_attributes(self):
        """clear_csrf_cookie should delete cookie with matching path and SameSite."""
        from gimnasioApp.auth_cookie import clear_csrf_cookie

        with override_settings(DEBUG=True):
            clear_csrf_cookie(self.response)

            cookie = self.response.cookies.get('csrftoken')
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, '')  # Empty value for deletion
            self.assertEqual(cookie['path'], '/')
            self.assertEqual(cookie['samesite'], 'Lax')

    def test_get_csrf_token_returns_token_from_request(self):
        """get_csrf_token should extract csrftoken from request cookies."""
        from gimnasioApp.auth_cookie import get_csrf_token

        factory = RequestFactory()
        request = factory.get('/')
        request.COOKIES['csrftoken'] = 'extracted-token'

        token = get_csrf_token(request)
        self.assertEqual(token, 'extracted-token')

    def test_get_csrf_token_returns_none_when_missing(self):
        """get_csrf_token should return None when cookie is not present."""
        from gimnasioApp.auth_cookie import get_csrf_token

        factory = RequestFactory()
        request = factory.get('/')
        # No csrftoken cookie set

        token = get_csrf_token(request)
        self.assertIsNone(token)