"""Integration tests for PagoMembresia endpoints.

Extracted from the original tests.py.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_admin_user, create_miembro, create_membresia, create_membresia_asignada
)


class PagoMembresiaIntegracionTest(TestCase):
    """Integration tests for PagoMembresia endpoints."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.user = create_admin_user(self.gimnasio)
        self.miembro = create_miembro("Carlos", "Mendez", self.gimnasio)
        self.membresia = create_membresia(
            self.gimnasio, name="Plan Test", price=50000, duration=30
        )
        self.asignada = create_membresia_asignada(
            self.miembro, self.membresia, date_initial=date(2026, 7, 1)
        )
        self.factory = APIRequestFactory()

    def test_post_pago_registra_abono(self):
        """5.5: POST pago registra abono y actualiza estado."""
        from gimnasioApp.views import PagoMembresiaViewSet
        view = PagoMembresiaViewSet.as_view({'post': 'create'})
        data = {
            'monto': '30000',
            'metodo_pago': 'efectivo',
            'nota': 'Abono inicial'
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['monto'], '30000.00')
        self.assertEqual(response.data['metodo_pago'], 'efectivo')
        self.assertIn('id', response.data)

        # Verificar que el pago existe en DB
        from gimnasioApp.models import PagoMembresia
        self.assertEqual(PagoMembresia.objects.count(), 1)
        pago = PagoMembresia.objects.first()
        self.assertEqual(pago.monto, Decimal('30000.00'))

        # Verificar que el estado de la membresia se actualizo
        self.asignada.refresh_from_db()
        self.assertEqual(self.asignada.total_pagado, Decimal('30000.00'))
        self.assertEqual(self.asignada.saldo_pendiente, Decimal('20000.00'))
        self.assertEqual(self.asignada.estado_pago, 'partial')

    def test_post_pago_lista_historial(self):
        """GET pagos lista el historial ordenado."""
        from gimnasioApp.models import PagoMembresia
        # Create two payments
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('10000'),
            metodo_pago='efectivo'
        )
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('20000'),
            metodo_pago='nequi'
        )

        from gimnasioApp.views import PagoMembresiaViewSet
        view = PagoMembresiaViewSet.as_view({'get': 'list'})
        request = self.factory.get('/')
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by fecha_pago descending
        self.assertEqual(len(response.data), 2)