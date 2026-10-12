"""Tests for DemoRequest model.

Extracted from the solicitud-demo implementation and adapted to use
the new tests package structure with factories.
"""

from django.test import TestCase

from .factories import (
    create_gimnasio, create_demo_request
)
from ..models import DemoRequest


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