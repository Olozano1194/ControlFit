"""Tests de integración: flow completo POST -> PATCH contactado -> provision.

Extracted from the solicitud-demo implementation and adapted to use
the new tests package structure with factories.
"""

from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from .factories import (
    create_gimnasio, create_user, create_demo_request
)
from ..models import DemoRequest, Usuario
from ..views.platform_views import DemoRequestViewSet
from ..services.onboarding import provision_gym_from_demo


class DemoRequestIntegrationTest(TestCase):
    """Tests de integración: flow completo POST -> PATCH contactado -> provision."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym 1")
        self.superadmin = create_user(
            email="super@test.com", name="Super", lastname="Admin",
            password="password123", gimnasio=self.gimnasio, roles="superadmin"
        )
        self.factory = APIRequestFactory()

    @patch('gimnasioApp.views.platform_views.send_welcome_email')
    def test_full_flow_post_then_patch_contactado_provisions(self, mock_email):
        # 1. POST público crea la solicitud
        view = DemoRequestViewSet.as_view({'post': 'create'})
        data = {
            'nombre': 'Ana López',
            'email': 'ana@demo.com',
            'telefono': '3009998877',
            'nombre_gimnasio': 'Gym Ana',
        }
        request = self.factory.post('/', data, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        demo_id = response.data['id']

        # 2. Superadmin PATCH estado a contactado -> provision
        demo = DemoRequest.objects.get(id=demo_id)
        view = DemoRequestViewSet.as_view({'patch': 'partial_update'})
        request = self.factory.patch('/', {'estado': 'contactado'}, format='json')
        request.user = self.superadmin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.superadmin)
        response = view(request, pk=demo_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'contactado')
        self.assertIsNotNone(response.data['gym_creado'])

        # 3. Verificar gym y admin creados
        demo.refresh_from_db()
        self.assertIsNotNone(demo.gym_creado)
        admin = Usuario.objects.get(email="ana@demo.com")
        self.assertEqual(admin.gimnasio, demo.gym_creado)
        self.assertTrue(admin.must_change_password)

    @patch('gimnasioApp.views.platform_views.send_welcome_email')
    def test_revert_flow_patch_pendiente_deprovisions(self, mock_email):
        # Setup: demo ya provisionada
        demo = create_demo_request(
            nombre="Test", email="test@revert.com", telefono="3000000000",
            nombre_gimnasio="Gym Test", estado="contactado"
        )
        provision_gym_from_demo(demo)
        self.assertIsNotNone(demo.gym_creado)

        # PATCH estado a pendiente -> revert
        view = DemoRequestViewSet.as_view({'patch': 'partial_update'})
        request = self.factory.patch('/', {'estado': 'pendiente'}, format='json')
        request.user = self.superadmin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.superadmin)
        response = view(request, pk=demo.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'pendiente')
        self.assertIsNone(response.data['gym_creado'])

        demo.refresh_from_db()
        self.assertIsNone(demo.gym_creado)
        self.assertEqual(demo.estado, 'pendiente')
        # Soft delete: user exists but is inactive
        admin = Usuario.all_objects.get(email="test@revert.com")
        self.assertFalse(admin.is_active)