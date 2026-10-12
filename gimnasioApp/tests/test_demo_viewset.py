"""Tests for DemoRequest ViewSet: POST público, GET/PATCH/DELETE superadmin.

Extracted from the solicitud-demo implementation and adapted to use
the new tests package structure with factories.
"""

from django.test import TestCase
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from .factories import (
    create_gimnasio, create_user, create_admin_user, create_demo_request
)
from ..models import DemoRequest
from ..views.platform_views import DemoRequestViewSet


class DemoRequestViewSetTest(TestCase):
    """Tests del ViewSet DemoRequest: POST público, GET/PATCH/DELETE superadmin."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym 1")
        self.superadmin = create_user(
            email="super@test.com", name="Super", lastname="Admin",
            password="password123", gimnasio=self.gimnasio, roles="superadmin"
        )
        self.admin = create_admin_user(self.gimnasio)
        self.factory = APIRequestFactory()

    def test_post_public_creates_demo_request(self):
        view = DemoRequestViewSet.as_view({'post': 'create'})
        data = {
            'nombre': 'Carlos',
            'email': 'carlos@test.com',
            'telefono': '3001112233',
            'nombre_gimnasio': 'Gym Carlos',
        }
        request = self.factory.post('/', data, format='json')
        # No auth - AllowAny
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Carlos')
        self.assertEqual(response.data['email'], 'carlos@test.com')
        self.assertEqual(response.data['estado'], 'pendiente')
        self.assertIsNone(response.data['gym_creado'])

    def test_post_requires_all_fields(self):
        view = DemoRequestViewSet.as_view({'post': 'create'})
        data = {'nombre': 'Carlos'}
        request = self.factory.post('/', data, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_list_requires_superadmin(self):
        view = DemoRequestViewSet.as_view({'get': 'list'})
        # Unauthenticated
        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Regular admin
        request = self.factory.get('/')
        request.user = self.admin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.admin)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Superadmin
        request = self.factory.get('/')
        request.user = self.superadmin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.superadmin)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_requires_superadmin(self):
        demo = create_demo_request(email="test@example.com", nombre_gimnasio="Test")
        view = DemoRequestViewSet.as_view({'patch': 'partial_update'})
        request = self.factory.patch('/', {'estado': 'contactado'}, format='json')
        request.user = self.superadmin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.superadmin)
        response = view(request, pk=demo.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'contactado')

    def test_delete_soft_delete_sets_cancelada(self):
        demo = create_demo_request(email="test@example.com", nombre_gimnasio="Test")
        view = DemoRequestViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete('/')
        request.user = self.superadmin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.superadmin)
        response = view(request, pk=demo.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        demo.refresh_from_db()
        self.assertEqual(demo.estado, 'cancelada')

    def test_delete_already_cancelled_returns_400(self):
        demo = create_demo_request(email="test@example.com", nombre_gimnasio="Test", estado='cancelada')
        view = DemoRequestViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete('/')
        request.user = self.superadmin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.superadmin)
        response = view(request, pk=demo.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cancelada', response.data['detail'])


class DemoRequestURLTest(TestCase):
    """Tests de registro de URLs."""

    def test_demo_request_url_registered_under_gym_api_v1(self):
        match = resolve('/gym/api/v1/solicitudes-demo/')
        self.assertEqual(match.func.cls.__name__, 'DemoRequestViewSet')
        self.assertTrue(match.route.startswith('gym/api/v1'))