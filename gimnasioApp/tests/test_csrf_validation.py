"""Tests for CSRF validation with log-only and enforce modes.

Extracted from tests.py lines 1397-1497.
"""

from unittest.mock import patch
from django.test import TestCase, RequestFactory


class CSRFValidationTest(TestCase):
    """Tests for validate_csrf function with log-only mode."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_request(self, method='POST', csrf_header=None, csrf_cookie=None):
        """Helper to create a request with optional CSRF header and cookie."""
        request = self.factory.generic(method, '/gym/api/v1/some-endpoint/')
        if csrf_header:
            request.META['HTTP_X_CSRF_TOKEN'] = csrf_header
        if csrf_cookie:
            request.COOKIES['csrftoken'] = csrf_cookie
        return request

    @patch('django.conf.settings.CSRF_ENFORCE', False)
    @patch('gimnasioApp.views.logger')
    def test_validate_csrf_log_only_mode_allows_missing_header(self, mock_logger):
        """In log-only mode (CSRF_ENFORCE=False), missing header should log but return True."""
        from gimnasioApp.views import validate_csrf

        request = self._make_request(method='POST', csrf_cookie='valid-token')
        result = validate_csrf(request)

        self.assertTrue(result)
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0]
        self.assertIn('CSRF validation failed', call_args[0])

    @patch('django.conf.settings.CSRF_ENFORCE', False)
    @patch('gimnasioApp.views.logger')
    def test_validate_csrf_log_only_mode_allows_mismatched_header(self, mock_logger):
        """In log-only mode, mismatched header should log but return True."""
        from gimnasioApp.views import validate_csrf

        request = self._make_request(method='POST', csrf_header='wrong-token', csrf_cookie='valid-token')
        result = validate_csrf(request)

        self.assertTrue(result)
        mock_logger.warning.assert_called()

    @patch('django.conf.settings.CSRF_ENFORCE', True)
    def test_validate_csrf_enforce_mode_rejects_missing_header(self):
        """In enforce mode (CSRF_ENFORCE=True), missing header should return False."""
        from gimnasioApp.views import validate_csrf

        request = self._make_request(method='POST', csrf_cookie='valid-token')
        result = validate_csrf(request)

        self.assertFalse(result)

    @patch('django.conf.settings.CSRF_ENFORCE', True)
    def test_validate_csrf_enforce_mode_rejects_mismatched_header(self):
        """In enforce mode, mismatched header should return False."""
        from gimnasioApp.views import validate_csrf

        request = self._make_request(method='POST', csrf_header='wrong-token', csrf_cookie='valid-token')
        result = validate_csrf(request)

        self.assertFalse(result)

    @patch('django.conf.settings.CSRF_ENFORCE', True)
    def test_validate_csrf_enforce_mode_allows_matching_header(self):
        """In enforce mode, matching header should return True."""
        from gimnasioApp.views import validate_csrf

        request = self._make_request(method='POST', csrf_header='matching-token', csrf_cookie='matching-token')
        result = validate_csrf(request)

        self.assertTrue(result)

    def test_validate_csrf_get_request_bypasses_validation(self):
        """GET requests should bypass CSRF validation entirely."""
        from gimnasioApp.views import validate_csrf

        request = self._make_request(method='GET', csrf_header=None, csrf_cookie=None)
        result = validate_csrf(request)

        self.assertTrue(result)

    def test_validate_csrf_put_patch_delete_require_validation(self):
        """PUT, PATCH, DELETE should require CSRF validation."""
        from gimnasioApp.views import validate_csrf

        for method in ['PUT', 'PATCH', 'DELETE']:
            with self.subTest(method=method):
                with patch('django.conf.settings.CSRF_ENFORCE', True):
                    request = self._make_request(method=method, csrf_header='token', csrf_cookie='token')
                    result = validate_csrf(request)
                    self.assertTrue(result)

                with patch('django.conf.settings.CSRF_ENFORCE', True):
                    request = self._make_request(method=method, csrf_header=None, csrf_cookie='token')
                    result = validate_csrf(request)
                    self.assertFalse(result)