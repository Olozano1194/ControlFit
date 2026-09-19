"""Tests for CSRF cookie being set/cleared on login, refresh, logout, register.

Extracted from tests.py lines 1499-1594.
"""

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase

from gimnasioApp.models import Gimnasio, Usuario


class AuthViewsCSRFCookieTest(TestCase):
    """Tests for CSRF cookie being set/cleared on login, refresh, logout."""

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

    def test_login_sets_csrf_cookie(self):
        """POST /token/ should set csrftoken cookie with correct attributes."""
        from gimnasioApp.views import CookieTokenObtainPairView

        request = self.factory.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')

        view = CookieTokenObtainPairView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertFalse(cookie['httponly'])
        self.assertEqual(cookie['path'], '/')
        self.assertEqual(cookie['max-age'], 86400)

    def test_refresh_sets_csrf_cookie(self):
        """POST /token/refresh/ should set csrftoken cookie with correct attributes."""
        from gimnasioApp.views import CookieTokenRefreshView

        refresh = RefreshToken.for_user(self.user)

        request = self.factory.post('/gym/api/v1/token/refresh/')
        request.COOKIES['refresh_token'] = str(refresh)

        view = CookieTokenRefreshView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertFalse(cookie['httponly'])
        self.assertEqual(cookie['path'], '/')

    def test_logout_clears_csrf_cookie(self):
        """POST /auth/logout/ should clear csrftoken cookie."""
        from gimnasioApp.views import LogoutView

        refresh = RefreshToken.for_user(self.user)

        request = self.factory.post('/gym/api/v1/auth/logout/')
        request.COOKIES['refresh_token'] = str(refresh)

        view = LogoutView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertEqual(cookie.value, '')  # Empty for deletion
        self.assertEqual(cookie['path'], '/')

    def test_register_sets_csrf_cookie(self):
        """POST /register/ should set csrftoken cookie with correct attributes."""
        from gimnasioApp.views import RegisterViewSet

        request = self.factory.post('/gym/api/v1/register/', {
            'email': 'newuser@example.com',
            'password': 'password123',
            'name': 'New',
            'lastname': 'User'
        }, format='json')

        view = RegisterViewSet.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertFalse(cookie['httponly'])
        self.assertEqual(cookie['path'], '/')
        self.assertEqual(cookie['max-age'], 86400)