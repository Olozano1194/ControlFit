"""Tests for DemoRequest serializer.

Extracted from the solicitud-demo implementation and adapted to use
the new tests package structure with factories.
"""

from django.test import TestCase

from .factories import (
    create_gimnasio, create_demo_request
)
from ..serializers.platform_serializer import DemoRequestSerializer


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