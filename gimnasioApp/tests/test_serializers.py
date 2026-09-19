"""Tests for serializer validation.

Extracted from the original tests.py (lines 1016-1127).
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from datetime import date, timedelta

from .factories import (
    create_gimnasio, create_user, create_miembro,
    create_membresia, create_membresia_asignada
)


class MembresiasSerializerTest(TestCase):
    """Tests for MembresiasSerializer."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.factory = APIRequestFactory()

    def _make_request(self):
        """Create a mock request with gimnasio."""
        request = self.factory.get('/')
        request.gimnasio = self.gimnasio
        return request

    # 6.6: MembresiasSerializer rejects duration=0 or duration=400
    def test_rejects_duration_zero(self):
        """Serializer should reject duration=0."""
        from gimnasioApp.serializers import MembresiasSerializer
        data = {
            "name": "Test Plan",
            "price": 100,
            "duration": 0,
            "max_multiplier": 1
        }
        serializer = MembresiasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("duration", serializer.errors)

    def test_rejects_duration_above_365(self):
        """Serializer should reject duration=400."""
        from gimnasioApp.serializers import MembresiasSerializer
        data = {
            "name": "Test Plan",
            "price": 100,
            "duration": 400,
            "max_multiplier": 1
        }
        serializer = MembresiasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("duration", serializer.errors)

    def test_accepts_valid_duration(self):
        """Serializer should accept duration=30."""
        from gimnasioApp.serializers import MembresiasSerializer
        data = {
            "name": "Test Plan",
            "price": 100,
            "duration": 30,
            "max_multiplier": 1
        }
        serializer = MembresiasSerializer(data=data, context={'request': self._make_request()})
        # Without gimnasio in context, create will fail, but validation should pass
        self.assertTrue(serializer.is_valid())

    def test_accepts_valid_duration_edge(self):
        """Serializer should accept duration=1 and duration=365."""
        from gimnasioApp.serializers import MembresiasSerializer
        for dur in [1, 365]:
            data = {
                "name": f"Plan {dur}",
                "price": 100,
                "duration": dur,
                "max_multiplier": 1
            }
            serializer = MembresiasSerializer(data=data, context={'request': self._make_request()})
            self.assertTrue(serializer.is_valid(), f"Duration {dur} should be valid")


class MembresiaAsignadaSerializerValidationTest(TestCase):
    """Tests for MembresiaAsignadaSerializer multiplier validation."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.membresia = create_membresia(
            self.gimnasio, name="Limited", price=10000, duration=30,
            max_multiplier=4
        )
        self.miembro = create_miembro("Test", "Member", self.gimnasio)
        self.factory = APIRequestFactory()

    def _make_request(self):
        """Create a mock request with gimnasio."""
        request = self.factory.get('/')
        request.gimnasio = self.gimnasio
        return request

    # 6.7: MembresiaAsignadaSerializer rejects multiplier > max_multiplier
    def test_serializer_rejects_multiplier_exceeds_max(self):
        """Serializer should reject multiplier > max_multiplier."""
        from gimnasioApp.serializers import MembresiaAsignadaSerializer
        data = {
            "miembro": self.miembro.id,
            "membresia": self.membresia.id,
            "multiplier": 5,  # max is 4
            "dateInitial": "2026-01-01"
        }
        serializer = MembresiaAsignadaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_serializer_accepts_valid_multiplier(self):
        """Serializer should accept multiplier <= max_multiplier."""
        from gimnasioApp.serializers import MembresiaAsignadaSerializer
        data = {
            "miembro": self.miembro.id,
            "membresia": self.membresia.id,
            "multiplier": 3,  # max is 4
            "dateInitial": (date.today() + timedelta(days=365)).isoformat()
        }
        serializer = MembresiaAsignadaSerializer(data=data, context={'request': self._make_request()})
        self.assertTrue(serializer.is_valid(), f"Errors: {serializer.errors}")