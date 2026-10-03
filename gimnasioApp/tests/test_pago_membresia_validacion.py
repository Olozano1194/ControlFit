"""Tests for PagoMembresia validacion de monto.

Extracted from the original tests.py.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_user, create_miembro, create_membresia, create_membresia_asignada
)


class PagoMembresiaValidacionTest(TestCase):
    """Tests for PagoMembresia validacion de monto."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.miembro = create_miembro("Juan", "Perez", self.gimnasio)
        self.membresia = create_membresia(
            self.gimnasio, name="Plan Test", price=100000, duration=30
        )
        self.asignada = create_membresia_asignada(
            self.miembro, self.membresia, date_initial=date(2026, 7, 1)
        )
        self.factory = APIRequestFactory()
        self.user = create_user(
            email="test@test.com", name="Test", lastname="User",
            password="pass123", gimnasio=self.gimnasio
        )

    def test_monto_no_excede_saldo_pendiente(self):
        """5.3: Validacion: monto no excede saldo_pendiente."""
        # saldo_pendiente = 100000
        # intentar pagar 150000 debe fallar
        self.assertGreater(Decimal('150000'), self.asignada.saldo_pendiente)

        # Verificar que el serializer rechaza el sobrepago
        data = {
            'membresia_asignada': self.asignada.id,
            'monto': 150000,
            'metodo_pago': 'efectivo',
            'nota': ''
        }
        request = self.factory.post('/')
        request.user = self.user
        request.gimnasio = self.gimnasio

        from gimnasioApp.serializers import PagoMembresiaSerializer
        serializer = PagoMembresiaSerializer(
            data=data,
            context={'request': request, 'membresia_asignada': self.asignada}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('monto', serializer.errors)

    def test_monto_cero_rechazado(self):
        """Monto = 0 debe ser rechazado."""
        data = {
            'membresia_asignada': self.asignada.id,
            'monto': 0,
            'metodo_pago': 'efectivo'
        }
        request = self.factory.post('/')
        request.user = self.user
        request.gimnasio = self.gimnasio

        from gimnasioApp.serializers import PagoMembresiaSerializer
        serializer = PagoMembresiaSerializer(
            data=data,
            context={'request': request, 'membresia_asignada': self.asignada}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('monto', serializer.errors)

    def test_monto_negativo_rechazado(self):
        """Monto negativo debe ser rechazado."""
        data = {
            'membresia_asignada': self.asignada.id,
            'monto': -100,
            'metodo_pago': 'efectivo'
        }
        request = self.factory.post('/')
        request.user = self.user
        request.gimnasio = self.gimnasio

        from gimnasioApp.serializers import PagoMembresiaSerializer
        serializer = PagoMembresiaSerializer(
            data=data,
            context={'request': request, 'membresia_asignada': self.asignada}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('monto', serializer.errors)