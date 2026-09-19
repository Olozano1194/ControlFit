"""Tests for POST /token/verify/ endpoint and integration flow.

Extracted from tests.py lines 1596-1830.
"""

import time
from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from gimnasioApp.models import Gimnasio, Usuario


class TokenVerifyEndpointTest(TestCase):
    """Tests for POST /token/verify/ endpoint."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def _make_verify_request(self, auth_header=None):
        """Helper to create a verify request with optional Authorization header."""
        request = self.factory.post('/gym/api/v1/token/verify/')
        if auth_header:
            request.META['HTTP_AUTHORIZATION'] = auth_header
        return request

    def test_verify_valid_token_returns_200_with_valid_and_exp(self):
        """Valid access token → 200 {valid: true, exp: timestamp}."""
        from gimnasioApp.views import CookieTokenVerifyView

        access = AccessToken.for_user(self.user)
        auth_header = f'Bearer {access}'

        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertTrue(response.data['valid'])
        self.assertIn('exp', response.data)
        self.assertIsInstance(response.data['exp'], int)
        # exp should be a Unix timestamp in the future
        self.assertGreater(response.data['exp'], int(time.time()))

    def test_verify_expired_token_returns_401(self):
        """Expired access token → 401."""
        from gimnasioApp.views import CookieTokenVerifyView

        # Create an already-expired token by manipulating exp
        access = AccessToken.for_user(self.user)
        # Manually set exp to past
        access.payload['exp'] = int((timezone.now() - timedelta(minutes=10)).timestamp())

        auth_header = f'Bearer {access}'

        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_invalid_malformed_token_returns_401(self):
        """Invalid/malformed token → 401."""
        from gimnasioApp.views import CookieTokenVerifyView

        auth_header = 'Bearer invalid.token.string'

        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_missing_authorization_header_returns_401(self):
        """Missing Authorization header → 401."""
        from gimnasioApp.views import CookieTokenVerifyView

        request = self._make_verify_request(auth_header=None)
        view = CookieTokenVerifyView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_without_bearer_prefix_returns_401(self):
        """Authorization header without Bearer prefix → 401."""
        from gimnasioApp.views import CookieTokenVerifyView

        access = AccessToken.for_user(self.user)
        auth_header = str(access)  # Missing "Bearer " prefix

        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_refresh_token_rejected(self):
        """Refresh token passed to verify endpoint → 401 (verify only accepts access tokens)."""
        from gimnasioApp.views import CookieTokenVerifyView

        refresh = RefreshToken.for_user(self.user)
        auth_header = f'Bearer {refresh}'

        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_old_long_lived_token_still_valid(self):
        """Backward compat: token issued with old 30min lifetime still verifies.

        Simulates a token created before the config change (old ACCESS_TOKEN_LIFETIME=30min).
        The verify endpoint should accept any valid, non-expired token regardless of
        which config was active when it was issued.
        """
        from gimnasioApp.views import CookieTokenVerifyView

        # Create a token with exp = now + 25 minutes (valid under old 30min config)
        access = AccessToken.for_user(self.user)
        access.payload['exp'] = int((timezone.now() + timedelta(minutes=25)).timestamp())

        auth_header = f'Bearer {access}'

        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertTrue(response.data['valid'])
        self.assertIn('exp', response.data)


class TokenVerifyIntegrationTest(TestCase):
    """Integration tests for token verify flow."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def test_login_then_verify_access_token_returns_200(self):
        """Integration: login → get access → call verify → 200."""
        from gimnasioApp.views import CookieTokenObtainPairView, CookieTokenVerifyView

        # Step 1: Login
        login_request = self.factory.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        login_view = CookieTokenObtainPairView.as_view()
        login_response = login_view(login_request)

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        access_token = login_response.data['access']

        # Step 2: Call verify with the access token
        verify_request = self.factory.post('/gym/api/v1/token/verify/')
        verify_request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        verify_view = CookieTokenVerifyView.as_view()
        verify_response = verify_view(verify_request)

        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['valid'])
        self.assertIn('exp', verify_response.data)

    def test_refresh_flow_does_not_affect_verify(self):
        """Refresh flow doesn't affect verify (verify uses access token, not refresh)."""
        from gimnasioApp.views import CookieTokenObtainPairView, CookieTokenRefreshView, CookieTokenVerifyView

        # Step 1: Login to get initial tokens
        login_request = self.factory.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        login_view = CookieTokenObtainPairView.as_view()
        login_response = login_view(login_request)

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        initial_access = login_response.data['access']
        refresh_cookie = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(refresh_cookie)

        # Step 2: Verify initial access token works
        verify_request = self.factory.post('/gym/api/v1/token/verify/')
        verify_request.META['HTTP_AUTHORIZATION'] = f'Bearer {initial_access}'
        verify_view = CookieTokenVerifyView.as_view()
        verify_response = verify_view(verify_request)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['valid'])

        # Step 3: Call refresh (rotates refresh token, returns new access)
        refresh_request = self.factory.post('/gym/api/v1/token/refresh/')
        refresh_request.COOKIES['refresh_token'] = refresh_cookie.value
        refresh_view = CookieTokenRefreshView.as_view()
        refresh_response = refresh_view(refresh_request)

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        new_access = refresh_response.data['access']

        # Step 4: Verify NEW access token works
        verify_request2 = self.factory.post('/gym/api/v1/token/verify/')
        verify_request2.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access}'
        verify_response2 = verify_view(verify_request2)
        self.assertEqual(verify_response2.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response2.data['valid'])

        # Step 5: Verify OLD access token still works (until expiry)
        verify_request3 = self.factory.post('/gym/api/v1/token/verify/')
        verify_request3.META['HTTP_AUTHORIZATION'] = f'Bearer {initial_access}'
        verify_response3 = verify_view(verify_request3)
        self.assertEqual(verify_response3.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response3.data['valid'])