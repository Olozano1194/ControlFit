"""Tests for DemoRequest model, API, and platform integration.

Extracted from the solicitud-demo implementation and adapted to use
the new tests package structure with factories.
"""

from unittest.mock import patch
from django.test import TestCase
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from .factories import (
    create_gimnasio, create_user, create_admin_user, create_demo_request
)
from ..models import DemoRequest, Gimnasio, Usuario
from ..serializers.platform_serializer import DemoRequestSerializer
from ..views.platform_views import DemoRequestViewSet, PlatformStatsView
from ..services.onboarding import provision_gym_from_demo, revert_gym_from_demo
from django.core.exceptions import ValidationError


class DemoRequestModelTest(TestCase):
    """Tests del modelo DemoRequest."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym for Demo")

    def test_create_demo_request_sets_fields(self):
        demo = create_demo_request(
            nombre="Juan Pérez",
            email="juan@test.com",
            telefono="3001234567",
            nombre_gimnasio="Mi Gimnasio",
        )
        self.assertEqual(demo.nombre, "Juan Pérez")
        self.assertEqual(demo.email, "juan@test.com")
        self.assertEqual(demo.telefono, "3001234567")
        self.assertEqual(demo.nombre_gimnasio, "Mi Gimnasio")
        self.assertEqual(demo.estado, "pendiente")
        self.assertIsNotNone(demo.fecha_solicitud)
        self.assertIsNone(demo.gym_creado)

    def test_demo_request_str(self):
        demo = create_demo_request(
            nombre="Test User",
            nombre_gimnasio="Test Gym"
        )
        self.assertEqual(str(demo), "Test Gym - Test User")

    def test_ordering_by_fecha_solicitud_desc(self):
        demo1 = create_demo_request(email="a@test.com", nombre_gimnasio="Gym A")
        import time
        time.sleep(0.01)  # Ensure different timestamps
        demo2 = create_demo_request(email="b@test.com", nombre_gimnasio="Gym B")
        demos = list(DemoRequest.objects.all())
        self.assertEqual(demos[0], demo2)  # Más reciente primero
        self.assertEqual(demos[1], demo1)


class DemoRequestSerializerTest(TestCase):
    """Tests del serializer DemoRequestSerializer."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym for Demo")

    def test_serializer_includes_gym_creado_nested(self):
        demo = create_demo_request(
            email="test@example.com",
            nombre_gimnasio="Test Gym",
            gym_creado=self.gimnasio
        )
        serializer = DemoRequestSerializer(demo)
        self.assertIn('gym_creado', serializer.data)
        self.assertEqual(serializer.data['gym_creado']['id'], self.gimnasio.id)
        self.assertEqual(serializer.data['gym_creado']['name'], self.gimnasio.name)

    def test_serializer_gym_creado_null_when_none(self):
        demo = create_demo_request(email="test@example.com", nombre_gimnasio="Test Gym")
        serializer = DemoRequestSerializer(demo)
        self.assertIsNone(serializer.data['gym_creado'])

    def test_serializer_email_sent_true_when_gym_created(self):
        demo = create_demo_request(
            email="test@example.com",
            nombre_gimnasio="Test Gym",
            gym_creado=self.gimnasio
        )
        serializer = DemoRequestSerializer(demo)
        self.assertTrue(serializer.data['email_sent'])

    def test_serializer_email_sent_false_when_no_gym(self):
        demo = create_demo_request(email="test@example.com", nombre_gimnasio="Test Gym")
        serializer = DemoRequestSerializer(demo)
        self.assertFalse(serializer.data['email_sent'])

    def test_validate_estado_rejects_cancelled(self):
        demo = create_demo_request(estado='cancelada')
        serializer = DemoRequestSerializer(demo, data={'estado': 'contactado'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('estado', serializer.errors)
        self.assertIn('cancelada', str(serializer.errors['estado']))

    def test_validate_estado_allows_pendiente_to_contactado(self):
        demo = create_demo_request(estado='pendiente')
        serializer = DemoRequestSerializer(demo, data={'estado': 'contactado'}, partial=True)
        self.assertTrue(serializer.is_valid())


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


class DemoRequestProvisionTest(TestCase):
    """Tests de provision_gym_from_demo y revert_gym_from_demo."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym 1")
        self.superadmin = create_user(
            email="super@test.com", name="Super", lastname="Admin",
            password="password123", gimnasio=self.gimnasio, roles="superadmin"
        )
        self.demo = create_demo_request(
            nombre="Juan Pérez",
            email="juan@demo.com",
            telefono="3001234567",
            nombre_gimnasio="Gym Juan",
            estado="pendiente"
        )

    @patch('gimnasioApp.views.platform_views.send_welcome_email')
    def test_provision_gym_from_demo_creates_gym_and_admin(self, mock_email):
        gym, admin, temp_pass = provision_gym_from_demo(self.demo)
        
        self.assertIsNotNone(gym)
        self.assertEqual(gym.name, "Gym Juan")
        self.assertTrue(gym.is_active)
        
        self.assertIsNotNone(admin)
        self.assertEqual(admin.email, "juan@demo.com")
        # Admin name is 'Admin' per implementation, lastname is gym name
        self.assertEqual(admin.name, "Admin")
        self.assertEqual(admin.lastname, "Gym Juan")
        self.assertEqual(admin.roles, "admin")
        self.assertEqual(admin.gimnasio, gym)
        self.assertTrue(admin.check_password(temp_pass))
        self.assertTrue(admin.must_change_password)
        
        self.demo.refresh_from_db()
        self.assertEqual(self.demo.gym_creado, gym)
        # Estado change to 'contactado' is done in ViewSet perform_update, not in provision
        # send_welcome_email is called via transaction.on_commit in ViewSet, not in provision

    @patch('gimnasioApp.views.platform_views.send_welcome_email')
    def test_provision_idempotent_when_gym_already_exists(self, mock_email):
        # Primera provision
        gym1, admin1, pass1 = provision_gym_from_demo(self.demo)
        
        # Segunda provision (estado ya contactado)
        gym2, admin2, pass2 = provision_gym_from_demo(self.demo)
        
        self.assertEqual(gym1, gym2)
        self.assertEqual(admin1, admin2)
        # Password is regenerated on each call (new temp password)
        self.assertNotEqual(pass1, pass2)
        mock_email.assert_not_called()  # No se reenvía email

    def test_revert_gym_from_demo_deletes_gym_and_admin(self):
        # Provision first
        provision_gym_from_demo(self.demo)
        gym = self.demo.gym_creado
        admin = Usuario.objects.get(email="juan@demo.com")
        
        # Revert
        revert_gym_from_demo(self.demo)
        
        self.demo.refresh_from_db()
        self.assertIsNone(self.demo.gym_creado)
        self.assertEqual(self.demo.estado, 'pendiente')
        
        # Soft delete: gym.is_active=False, admin.is_active=False
        gym.refresh_from_db()
        self.assertFalse(gym.is_active)
        admin.refresh_from_db()
        self.assertFalse(admin.is_active)


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


class DemoRequestURLTest(TestCase):
    """Tests de registro de URLs."""

    def test_demo_request_url_registered_under_gym_api_v1(self):
        match = resolve('/gym/api/v1/solicitudes-demo/')
        self.assertEqual(match.func.cls.__name__, 'DemoRequestViewSet')
        self.assertTrue(match.route.startswith('gym/api/v1'))