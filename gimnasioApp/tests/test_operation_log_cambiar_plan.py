"""Tests for cambiar_plan endpoint audit log integration.

Integration tests for cambiar_plan endpoint with OperationLog - written first to fail (RED).
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


class OperationLogCambiarPlanEndpointTest(TestCase):
    """Tests for cambiar_plan endpoint audit log integration."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.user = create_admin_user(self.gimnasio)
        self.miembro = create_miembro("Carlos", "Mendez", self.gimnasio)

        self.membresia_actual = create_membresia(
            self.gimnasio, name="Plan Actual", price=50000, duration=30, max_multiplier=12
        )

        self.membresia_nueva = create_membresia(
            self.gimnasio, name="Plan Nuevo", price=75000, duration=45, max_multiplier=8
        )

        self.asignada = create_membresia_asignada(
            self.miembro, self.membresia_actual,
            date_initial=date(2026, 7, 1),
            multiplier=1,
            discount=0
        )
        self.factory = APIRequestFactory()

    def test_cambiar_plan_creates_log(self):
        """REQ-1: cambiar_plan success creates an OperationLog with correct fields."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from datetime import date

        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'nueva_membresia_id': self.membresia_nueva.id,
            'reason': 'Cliente quiere cambiar a plan premium',
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_after, count_before + 1)

        log = OperationLog.objects.latest('created_at')
        self.assertEqual(log.operation_type, 'cambiar_plan')
        self.assertEqual(log.reason, 'Cliente quiere cambiar a plan premium')
        self.assertEqual(log.usuario, self.user)
        self.assertEqual(log.gimnasio, self.gimnasio)
        self.assertEqual(log.membresia_asignada, self.asignada)
        self.assertIn('membresia_anterior', log.details)
        self.assertIn('membresia_nueva', log.details)
        self.assertIn('credit', log.details)
        self.assertIn('final_price', log.details)
        self.assertEqual(log.details['membresia_anterior'], self.membresia_actual.id)
        self.assertEqual(log.details['membresia_nueva'], self.membresia_nueva.id)

    def test_cambiar_plan_rejected_no_log(self):
        """REQ-1: rejected cambiar_plan creates no OperationLog."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet

        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'nueva_membresia_id': self.membresia_nueva.id,
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