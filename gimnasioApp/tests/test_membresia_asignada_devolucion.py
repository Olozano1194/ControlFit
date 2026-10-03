"""Tests for MembresiaAsignada devolucion (refund) action."""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_admin_user, create_user, create_miembro, create_membresia, create_membresia_asignada
)


class MembresiaAsignadaDevolucionTest(TestCase):
    """Tests for MembresiaAsignada devolucion (refund) action."""

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

    def test_devolucion_requires_reason(self):
        """Devolucion should require 'reason' field."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '10000',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_devolucion_requires_monto(self):
        """Devolucion should require 'monto' field."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'reason': 'Cliente solicita devolución por insatisfacción',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('monto', response.data)

    def test_devolucion_reason_min_length(self):
        """Devolucion should require reason with at least 10 characters."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '10000',
            'reason': 'Corto',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_devolucion_monto_positive(self):
        """Devolucion should require monto > 0."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '0',
            'reason': 'Cliente solicita devolución por insatisfacción',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('monto', response.data)

    def test_devolucion_monto_not_exceed_saldo_pendiente(self):
        """Devolucion should not allow monto > saldo_pendiente."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from gimnasioApp.models import PagoMembresia
        from decimal import Decimal
        
        # Make a partial payment so saldo_pendiente is known
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('20000'),
            metodo_pago='efectivo'
        )
        self.asignada.refresh_from_db()
        
        # saldo_pendiente = 50000 - 20000 = 30000
        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '40000',  # Exceeds saldo_pendiente of 30000
            'reason': 'Cliente solicita devolución por insatisfacción',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('monto', response.data)

    def test_devolucion_creates_negative_payment(self):
        """Devolucion should create a negative payment record (or equivalent).
        
        The refund reduces total_pagado, recomputes saldo_pendiente and estado_pago.
        """
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from gimnasioApp.models import PagoMembresia
        from decimal import Decimal
        
        # Make a payment so there's something to refund
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('30000'),
            metodo_pago='efectivo'
        )
        self.asignada.refresh_from_db()
        
        original_total_pagado = self.asignada.total_pagado
        original_saldo_pendiente = self.asignada.saldo_pendiente
        original_estado_pago = self.asignada.estado_pago
        
        # saldo_pendiente = 20000, we refund 10000
        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '10000',
            'reason': 'Cliente solicita devolución parcial por insatisfacción',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify refund was processed
        self.asignada.refresh_from_db()
        
        # total_pagado should be reduced by refund amount
        self.assertEqual(self.asignada.total_pagado, original_total_pagado - Decimal('10000'))
        
        # saldo_pendiente should be recomputed: price - new_total_pagado
        self.assertEqual(self.asignada.saldo_pendiente, self.asignada.price - self.asignada.total_pagado)
        
        # estado_pago should be recomputed
        if self.asignada.total_pagado >= self.asignada.price:
            expected_estado = 'paid'
        elif self.asignada.total_pagado > 0:
            expected_estado = 'partial'
        else:
            expected_estado = 'pending'
        self.assertEqual(self.asignada.estado_pago, expected_estado)
        
        # Response should contain updated assignment
        self.assertIn('total_pagado', response.data)
        self.assertIn('saldo_pendiente', response.data)
        self.assertIn('estado_pago', response.data)
        self.assertEqual(float(response.data['total_pagado']), float(self.asignada.total_pagado))
        self.assertEqual(float(response.data['saldo_pendiente']), float(self.asignada.saldo_pendiente))
        self.assertEqual(response.data['estado_pago'], self.asignada.estado_pago)

    def test_devolucion_full_refund_to_pending(self):
        """Full refund should set estado_pago back to 'pending'."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from gimnasioApp.models import PagoMembresia
        from decimal import Decimal
        
        # Make a full payment so estado_pago = 'paid'
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('50000'),
            metodo_pago='efectivo'
        )
        self.asignada.refresh_from_db()
        self.assertEqual(self.asignada.estado_pago, 'paid')
        
        # Full refund
        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '50000',
            'reason': 'Devolución completa por cancelación de servicio',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.asignada.refresh_from_db()
        self.assertEqual(self.asignada.total_pagado, Decimal('0'))
        self.assertEqual(self.asignada.estado_pago, 'pending')
        self.assertEqual(self.asignada.saldo_pendiente, self.asignada.price)

    def test_devolucion_multi_tenant_isolation(self):
        """Devolucion should only work within the same gimnasio."""
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

        view = MembresiaAsignadaViewSet.as_view({'post': 'devolucion'})
        data = {
            'monto': '10000',
            'reason': 'Devolución por insatisfacción',
        }
        request = self.factory.post('/', data)
        request.user = self.user  # User from gym1
        request.gimnasio = self.gimnasio  # Gym1
        force_authenticate(request, user=self.user)

        # Try to refund assignment from gym2
        response = view(request, pk=asignada2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)