"""Tests for MembresiaAsignada cambiar-plan action.

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


class MembresiaAsignadaCambiarPlanTest(TestCase):
    """Tests for MembresiaAsignada cambiar-plan action."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.user = create_admin_user(self.gimnasio)
        self.miembro = create_miembro("Carlos", "Mendez", self.gimnasio)
        
        # Current plan: 30 days, price 50000
        self.membresia_actual = create_membresia(
            self.gimnasio, name="Plan Actual", price=50000, duration=30, max_multiplier=12
        )
        
        # New plan: 45 days, price 75000
        self.membresia_nueva = create_membresia(
            self.gimnasio, name="Plan Nuevo", price=75000, duration=45, max_multiplier=8
        )
        
        # Assignment started 2026-07-01, today is 2026-07-15 (14 days used, 16 days remaining)
        # Using a fixed date for testing
        self.asignada = create_membresia_asignada(
            self.miembro, self.membresia_actual, 
            date_initial=date(2026, 7, 1),
            multiplier=1,
            discount=0
        )
        # dateFinal = 2026-07-31 (30 days from 2026-07-01)
        # price = 50000
        self.factory = APIRequestFactory()

    def test_cambiar_plan_requires_reason(self):
        """Cambiar plan should require 'reason' field."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'nueva_membresia_id': self.membresia_nueva.id,
            'multiplier': 1,
            'discount_percent': 0,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_cambiar_plan_requires_nueva_membresia_id(self):
        """Cambiar plan should require 'nueva_membresia_id' field."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'reason': 'Cliente quiere cambiar a plan premium',
            'multiplier': 1,
            'discount_percent': 0,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nueva_membresia_id', response.data)

    def test_cambiar_plan_reason_min_length(self):
        """Cambiar plan should require reason with at least 10 characters."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'nueva_membresia_id': self.membresia_nueva.id,
            'reason': 'Corto',
            'multiplier': 1,
            'discount_percent': 0,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_cambiar_plan_calculates_unused_days_credit(self):
        """Cambiar plan should calculate credit from unused days of current plan.
        
        Current plan: 50000 for 30 days = 1666.67/day
        Started 2026-07-01, today 2026-07-15 = 14 days used, 16 days unused
        Credit = 16 * 1666.67 = 26666.67
        """
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

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 7, 15))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify credit was applied - new plan total should be reduced by credit
        # New plan price = 75000
        # Credit = 16 * (50000/30) = 26666.67
        # Expected new price = 75000 - 26666.67 = 48333.33
        self.assertIn('price', response.data)
        self.assertIn('dateFinal', response.data)
        self.assertIn('membresia', response.data)
        
        # New membership should be the new one
        self.assertEqual(response.data['membresia'], self.membresia_nueva.id)
        
        # dateInitial should be today (2026-07-15)
        # dateFinal should be today + 45 days * 1 = 2026-08-29
        self.assertEqual(response.data['dateInitial'], '15-07-2026')  # format DD-MM-YYYY
        
        # price should reflect credit applied
        # We'll check that it's less than the full new plan price
        self.assertLess(float(response.data['price']), float(self.membresia_nueva.price))
        
        # Verify credit calculation: ~26666.67 credit applied
        expected_price = float(self.membresia_nueva.price) - 26666.67
        self.assertAlmostEqual(float(response.data['price']), expected_price, places=1)

    def test_cambiar_plan_preserves_snapshots(self):
        """Cambiar plan should preserve accounting snapshots (total_pagado unchanged).
        
        Note: price changes to new credit-adjusted price, so saldo_pendiente and estado_pago
        are RECOMPUTED from new price + existing payments. This is correct behavior -
        the member's remaining balance reflects the new plan price after credit.
        """
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from gimnasioApp.models import PagoMembresia
        from decimal import Decimal
        from datetime import date
        
        # Make a partial payment so estado_pago = 'partial'
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('20000'),
            metodo_pago='efectivo'
        )
        self.asignada.refresh_from_db()
        
        original_total_pagado = self.asignada.total_pagado
        original_saldo_pendiente = self.asignada.saldo_pendiente
        original_estado_pago = self.asignada.estado_pago
        
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

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 7, 15))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # total_pagado should be preserved (actual payments don't change)
        self.assertEqual(float(response.data['total_pagado']), float(original_total_pagado))
        
        # saldo_pendiente and estado_pago are RECOMPUTED from new price
        # New price = 75000 - 26666.67 = 48333.33
        # total_pagado = 20000
        # New saldo_pendiente = 48333.33 - 20000 = 28333.33
        # New estado_pago = 'partial' (20000 < 48333.33)
        self.assertNotEqual(float(response.data['saldo_pendiente']), float(original_saldo_pendiente))
        self.assertEqual(response.data['estado_pago'], 'partial')  # still partial
        
        # Verify the new saldo_pendiente is correct
        expected_new_saldo = float(response.data['price']) - float(original_total_pagado)
        self.assertAlmostEqual(float(response.data['saldo_pendiente']), expected_new_saldo, places=1)

    def test_cambiar_plan_with_multiplier_and_discount(self):
        """Cambiar plan should apply multiplier and discount_percent from operation."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from datetime import date
        
        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'nueva_membresia_id': self.membresia_nueva.id,
            'reason': 'Cliente quiere cambiar a plan premium con 2x',
            'multiplier': 2,
            'discount_percent': 10,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 7, 15))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # New plan: 75000 * 2 * (1 - 10/100) = 150000 * 0.9 = 135000
        # Credit: 16 * (50000/30) = 26666.67
        # Expected: 135000 - 26666.67 = 108333.33
        self.assertLess(float(response.data['price']), float(self.membresia_nueva.price * 2))
        
        # dateFinal should be today + 45 * 2 = 90 days = 2026-10-13
        self.assertEqual(response.data['multiplier'], '2.0')
        self.assertEqual(response.data['discount_percent'], '10.00')
        
        # Verify price calculation
        expected_price = 135000 - 26666.67
        self.assertAlmostEqual(float(response.data['price']), expected_price, places=1)

    def test_cambiar_plan_multi_tenant_isolation(self):
        """Cambiar plan should only work within the same gimnasio."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from datetime import date
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
        
        membresia_nueva_gym2 = create_membresia(
            gym2, name="Plan Nuevo Gym2", price=75000, duration=45
        )

        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'nueva_membresia_id': membresia_nueva_gym2.id,
            'reason': 'Cliente quiere cambiar de plan',
            'multiplier': 1,
            'discount_percent': 0,
        }
        request = self.factory.post('/', data)
        request.user = self.user  # User from gym1
        request.gimnasio = self.gimnasio  # Gym1
        force_authenticate(request, user=self.user)

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 7, 15))
        response = view(request, pk=asignada2.id)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cambiar_plan_validates_max_multiplier(self):
        """Cambiar plan should validate multiplier against new plan's max_multiplier."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from datetime import date
        # New plan has max_multiplier=8
        view = MembresiaAsignadaViewSet.as_view({'post': 'cambiar_plan'})
        data = {
            'nueva_membresia_id': self.membresia_nueva.id,
            'reason': 'Cliente quiere cambiar a plan premium con multiplier 10',
            'multiplier': 10,  # Exceeds max_multiplier of 8
            'discount_percent': 0,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 7, 15))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should have validation error about multiplier
        self.assertTrue(
            'multiplier' in str(response.data) or 'non_field_errors' in str(response.data)
        )

    def test_cambiar_plan_returns_updated_assignment(self):
        """Cambiar plan should return the updated assignment with all fields."""
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

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 7, 15))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return full assignment data
        expected_fields = [
            'id', 'miembro', 'membresia', 'miembro_details', 'membresia_details',
            'dateInitial', 'dateFinal', 'price', 'multiplier', 'discount_percent',
            'total_pagado', 'saldo_pendiente', 'estado_pago'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data, f"Missing field: {field}")