"""Integration test for end-to-end avatar upload.

Extracted from the original tests.py (lines 366-421).
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from .factories import create_gimnasio, create_user
from .helpers import make_uploaded_image


class AvatarUploadIntegrationTest(TestCase):
    """Integration test for end-to-end avatar upload."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.user = create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            roles="admin",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def test_avatar_upload_returns_url(self):
        """PATCH /api/user/ with avatar should return the avatar URL."""
        mock_storage = MagicMock()
        mock_storage.url.return_value = 'https://test-project.supabase.co/storage/v1/object/public/fotos/test.jpg'
        mock_storage.save.return_value = 'fotos/test.jpg'
        mock_storage.exists.return_value = False

        # Patch the storage used by the avatar field
        with patch.object(__import__('gimnasioApp.models', fromlist=['Usuario']).Usuario.avatar.field, 'storage', mock_storage):
            new_avatar = make_uploaded_image('test.jpg')
            from gimnasioApp.views import UserViewSet
            view = UserViewSet.as_view({'patch': 'partial_update'})
            request = self.factory.patch('/api/user/', {'avatar': new_avatar}, format='multipart')
            request.user = self.user
            request.gimnasio = self.gimnasio
            force_authenticate(request, user=self.user)

            with patch.object(UserViewSet, 'get_object', return_value=self.user):
                response = view(request, pk=self.user.id)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # Assert response contains Supabase URL (starts with 'http')
                self.assertIn('avatar', response.data)
                avatar_url = response.data['avatar']
                self.assertTrue(avatar_url.startswith('http'), f"Avatar URL should start with 'http', got: {avatar_url}")