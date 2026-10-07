"""Tests for renovar endpoint audit log integration.

Integration tests for renovar endpoint with OperationLog - written first to fail (RED).
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


class OperationLogRenovarEndpointTest(TestCase):
    """Tests for renovar endpoint audit log integration."""

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

    def test_renovar_creates_log(self):
        """REQ-1: renovar success creates an OperationLog with correct fields."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from datetime import date

        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'reason': 'Renovación anual por cliente fiel',
            'multiplier': 1,
            'discount_percent': 0,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        view.cls.get_today = classmethod(lambda cls: date(2026, 7, 15))

        count_before = OperationLog.objects.count()
        response = view(request, pk=self.asignada.id)
        count_after = OperationLog.objects.count()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(count_after, count_before + 1)

        log = OperationLog.objects.latest('created_at')
        self.assertEqual(log.operation_type, 'renovar')
        self.assertEqual(log.reason, 'Renovación anual por cliente fiel')
        self.assertEqual(log.usuario, self.user)
        self.assertEqual(log.gimnasio, self.gimnasio)
        self.assertEqual(log.membresia_asignada, self.asignada)
        self.assertEqual(log.membresia_asignada_id, self.asignada.id)
        self.assertIn('nueva_asignacion_id', log.details)
        self.assertIn('membresia', log.details)
        self.assertIn('price', log.details)
        self.assertEqual(log.details['membresia'], self.membresia.id)

    def test_renovar_rejected_no_log(self):
        """REQ-1: rejected renovar creates no OperationLog."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet

        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
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