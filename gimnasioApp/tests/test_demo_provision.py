"""Tests for provision_gym_from_demo and revert_gym_from_demo.

Extracted from the solicitud-demo implementation and adapted to use
the new tests package structure with factories.
"""

from unittest.mock import patch
from django.test import TestCase

from .factories import (
    create_gimnasio, create_user, create_demo_request
)
from ..models import DemoRequest, Usuario
from ..services.onboarding import provision_gym_from_demo, revert_gym_from_demo


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