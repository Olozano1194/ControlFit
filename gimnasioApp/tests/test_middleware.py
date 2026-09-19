"""Tests for GimnasioMiddleware.

Extracted from the original tests.py (lines 25-71).
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser

from .factories import create_gimnasio, create_user


class GimnasioMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        from gimnasioApp.middleware import GimnasioMiddleware
        self.middleware = GimnasioMiddleware(lambda r: None)

    def test_authenticated_user_gets_gimnasio(self):
        gimnasio = create_gimnasio(name="Test Gym")
        user = create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=gimnasio
        )
        request = self.factory.get('/')
        request.user = user
        self.middleware(request)
        self.assertEqual(request.gimnasio, gimnasio)

    def test_anonymous_user_gets_none(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.middleware(request)
        self.assertIsNone(request.gimnasio)

    def test_user_without_gimnasio_gets_none(self):
        gimnasio = create_gimnasio(name="Test Gym 2")
        user = create_user(
            email="nogym@example.com",
            name="No",
            lastname="Gym",
            password="password123",
            gimnasio=gimnasio
        )

        # Test middleware with user whose gimnasio is None
        request = self.factory.get('/')
        request.user = user
        user.gimnasio = None
        self.middleware(request)
        self.assertIsNone(request.gimnasio)