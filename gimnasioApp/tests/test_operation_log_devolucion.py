"""Tests for devolucion endpoint audit log integration.

Integration tests for devolucion endpoint with OperationLog - written first to fail (RED).
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_admin_user, create_user, create_miembro,
    create_membresia, create_membresia_asignada
)


class OperationLogDevolucionEndpointTest(TestCase):
    """Tests for devolucion endpoint audit log integration."""

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
        from gimnasioApp.models import PagoMembresia
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('20000'),
            metodo_pago='efectivo'
        )
        self.factory = APIRequestFactory()

    def test_devolucion_creates_log(self):
        """REQ-1: devolucion success creates an OperationLog with correct fields."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet

        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '10000',
            'reason': 'Devolución por insatisfacción del cliente',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        total_pagado_before = self.asignada.total_pagado

        count_before = OperationLog.objects.count()
        response = view(request, pk=self.asignada.id)
        count_after = OperationLog.objects.count()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_after, count_before + 1)

        log = OperationLog.objects.latest('created_at')
        self.assertEqual(log.operation_type, 'devolucion')
        self.assertEqual(log.reason, 'Devolución por insatisfacción del cliente')
        self.assertEqual(log.usuario, self.user)
        self.assertEqual(log.gimnasio, self.gimnasio)
        self.assertEqual(log.membresia_asignada, self.asignada)
        self.assertIn('monto', log.details)
        self.assertIn('total_pagado_before', log.details)
        self.assertEqual(log.details['monto'], '10000')
        self.assertEqual(log.details['total_pagado_before'], str(total_pagado_before))

    def test_devolucion_rejected_no_log(self):
        """REQ-1: rejected devolucion creates no OperationLog."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet

        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '10000',
            # Missing required 'reason' field
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        count_before = OperationLog.objects.count()
        response = view(request, pk=self.asignada.id)
        count_after = OperationLog.objects.count()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(count_after, count_before)