"""Tests for MembresiaAsignada suspender action.

Extracted from the original tests.py.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_admin_user, create_user, create_miembro, create_membresia, create_membresia_asignada
)


class MembresiaAsignadaSuspenderTest(TestCase):
    """Tests for MembresiaAsignada suspender action."""

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

    def test_suspender_requires_reason(self):
        """Suspender action should require 'reason' field."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'suspender'})
        data = {
            'fecha_inicio': '2026-07-15',
            'fecha_fin': '2026-08-15',
            'dias': 30,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_suspender_with_reason_updates_dates(self):
        """Suspender with reason should update dateFinal and return updated assignment."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'suspender'})
        data = {
            'fecha_inicio': '2026-07-15',
            'fecha_fin': '2026-08-15',
            'dias': 30,
            'reason': 'Licencia médica',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('dateFinal', response.data)
        self.assertEqual(response.data['estado_pago'], self.asignada.estado_pago)

    def test_suspender_multi_tenant_isolation(self):
        """Suspender should only work within the same gimnasio."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        gym2 = create_gimnasio(name="Gym 2")
        user2 = create_user(
            email="admin2@example.com", name="Admin", lastname="User",
            password="password123", gimnasio=gym2, roles="admin"
        )
        miembro2 = create_miembro("Otro", "Usuario", gym2)
        membresia2 = create_membresia(
            gym2, name="Plan 2", price=50000, duration=30
        )
        asignada2 = create_membresia_asignada(
            miembro2, membresia2, date_initial=date(2026, 7, 1)
        )

        view = MembresiaAsignadaViewSet.as_view({'post': 'suspender'})
        data = {
            'fecha_inicio': '2026-07-15',
            'fecha_fin': '2026-08-15',
            'dias': 30,
            'reason': 'Licencia médica',
        }
        request = self.factory.post('/', data)
        request.user = self.user  # User from gym1
        request.gimnasio = self.gimnasio  # Gym1
        force_authenticate(request, user=self.user)

        # Try to suspend assignment from gym2
        response = view(request, pk=asignada2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)