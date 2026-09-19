"""Integration tests for CSRF enforcement at endpoint level (CSRF_ENFORCE=True).

Uses Django test client (self.client) which runs through the full middleware stack.

Extracted from tests.py lines 1832-2015.
"""

from rest_framework import status
from django.test import TestCase

from gimnasioApp.models import Gimnasio, Usuario


class CSRFEnforcementIntegrationTest(TestCase):
    """Integration tests for CSRF enforcement at endpoint level (CSRF_ENFORCE=True).

    Uses Django test client (self.client) which runs through the full middleware stack.
    """

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )

    def _login_and_get_tokens(self):
        """Helper: login via test client and return access token, refresh cookie, csrf cookie."""
        login_response = self.client.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        refresh_cookie = login_response.cookies.get('refresh_token')
        csrf_cookie = login_response.cookies.get('csrftoken')

        return access_token, refresh_cookie.value if refresh_cookie else None, csrf_cookie.value if csrf_cookie else None

    def test_csrf_missing_header_returns_403(self):
        """POST mutating request without X-CSRF-Token header → 403."""
        access_token, _, csrf_token = self._login_and_get_tokens()

        # Make a mutating request WITHOUT X-CSRF-Token header
        response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'New', 'lastname': 'Member'
        }, format='json', HTTP_AUTHORIZATION=f'Bearer {access_token}')
        # No HTTP_X_CSRF_TOKEN header

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csrf_invalid_header_returns_403(self):
        """POST mutating request with mismatched X-CSRF-Token header → 403."""
        access_token, _, csrf_token = self._login_and_get_tokens()

        # Make a mutating request with WRONG X-CSRF-Token header
        response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'New', 'lastname': 'Member'
        }, format='json',
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN='wrong-token')  # Mismatched

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csrf_valid_header_allows_request(self):
        """POST mutating request with matching X-CSRF-Token header → 201."""
        access_token, _, csrf_token = self._login_and_get_tokens()

        # Make a mutating request with CORRECT X-CSRF-Token header
        # The test client automatically sends cookies from previous responses
        response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'New', 'lastname': 'Member', 'phone': '3001234567', 'address': 'Calle 123'
        }, format='json',
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN=csrf_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_request_bypasses_csrf(self):
        """GET requests should bypass CSRF validation even without header."""
        access_token, _, _ = self._login_and_get_tokens()

        # GET request without X-CSRF-Token header
        response = self.client.get('/gym/api/v1/UserGym/',
        HTTP_AUTHORIZATION=f'Bearer {access_token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_patch_delete_require_csrf(self):
        """PUT, PATCH, DELETE should require CSRF validation."""
        access_token, _, csrf_token = self._login_and_get_tokens()

        # First create a member to update/delete
        create_response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'ToUpdate', 'lastname': 'Member', 'phone': '3001234567', 'address': 'Calle 123'
        }, format='json',
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN=csrf_token)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        member_id = create_response.data['id']

        for method in ['put', 'patch', 'delete']:
            with self.subTest(method=method):
                # Request WITHOUT CSRF token
                if method == 'delete':
                    response = self.client.delete(f'/gym/api/v1/UserGym/{member_id}/',
                    HTTP_AUTHORIZATION=f'Bearer {access_token}')
                else:
                    response = getattr(self.client, method)(f'/gym/api/v1/UserGym/{member_id}/', {
                        'name': 'Updated', 'lastname': 'Member'
                    }, format='json', HTTP_AUTHORIZATION=f'Bearer {access_token}')

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                               f"{method.upper()} without CSRF should return 403")


class FullAuthFlowIntegrationTest(TestCase):
    """Integration test: full login → mutate → refresh flow.

    Uses Django test client (self.client) which runs through the full middleware stack.
    """

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )

    def test_full_login_mutate_refresh_flow(self):
        """Full flow: login → create member (mutate) → refresh → verify token still works."""
        from gimnasioApp.views import CookieTokenVerifyView

        # Step 1: Login
        login_response = self.client.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        refresh_cookie = login_response.cookies.get('refresh_token')
        csrf_token = login_response.cookies.get('csrftoken')
        self.assertIsNotNone(refresh_cookie)
        self.assertIsNotNone(csrf_token)

        # Step 2: Verify initial access token
        verify_response = self.client.post('/gym/api/v1/token/verify/',
        HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['valid'])

        # Step 3: Mutating request with CSRF (create member)
        create_response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'Integration', 'lastname': 'Test', 'phone': '3001234567', 'address': 'Calle 123'
        }, format='json',
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN=csrf_token.value)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        member_id = create_response.data['id']

        # Step 4: Refresh access token
        refresh_response = self.client.post('/gym/api/v1/token/refresh/',
        HTTP_COOKIE=f'refresh_token={refresh_cookie.value}')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        new_access = refresh_response.data['access']
        new_csrf_token = refresh_response.cookies.get('csrftoken')
        self.assertIsNotNone(new_csrf_token)

        # Step 5: Verify NEW access token works
        verify_response2 = self.client.post('/gym/api/v1/token/verify/',
        HTTP_AUTHORIZATION=f'Bearer {new_access}')
        self.assertEqual(verify_response2.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response2.data['valid'])

        # Step 6: Mutating request with NEW CSRF token (update member)
        update_response = self.client.patch(f'/gym/api/v1/UserGym/{member_id}/', {
            'name': 'Updated'
        }, format='json', content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {new_access}',
        HTTP_X_CSRF_TOKEN=new_csrf_token.value)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['name'], 'Updated')

        # Step 7: Verify token verify still works after mutation
        verify_response3 = self.client.post('/gym/api/v1/token/verify/',
        HTTP_AUTHORIZATION=f'Bearer {new_access}')
        self.assertEqual(verify_response3.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response3.data['valid'])