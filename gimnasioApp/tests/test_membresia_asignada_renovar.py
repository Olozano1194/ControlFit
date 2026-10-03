"""Tests for MembresiaAsignada renovar (renew) action."""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_admin_user, create_user, create_miembro, create_membresia, create_membresia_asignada
)


class MembresiaAsignadaRenovarTest(TestCase):
    """Tests for MembresiaAsignada renovar (renew) action."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.user = create_admin_user(self.gimnasio)
        self.miembro = create_miembro("Carlos", "Mendez", self.gimnasio)
        self.membresia = create_membresia(
            self.gimnasio, name="Plan Test", price=50000, duration=30, max_multiplier=12
        )
        self.asignada = create_membresia_asignada(
            self.miembro, self.membresia, date_initial=date(2026, 7, 1)
        )
        self.factory = APIRequestFactory()

    def test_renovar_requires_reason(self):
        """Renovar should require 'reason' field."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'membresia_id': self.membresia.id,
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_renovar_reason_min_length(self):
        """Renovar should require reason with at least 10 characters."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'membresia_id': self.membresia.id,
            'reason': 'Corto',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_renovar_creates_new_assignment(self):
        """Renovar should create a NEW assignment (not modify existing).
        
        Preferred over modifying existing assignment.
        Returns the new assignment.
        """
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from gimnasioApp.models import MembresiaAsignada
        from datetime import date
        
        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'membresia_id': self.membresia.id,
            'reason': 'Renovación mensual del cliente',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        # Override get_today to return fixed test date (assignment ends 2026-07-31)
        view.cls.get_today = classmethod(lambda cls: date(2026, 8, 1))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Should return new assignment data
        self.assertIn('id', response.data)
        self.assertIn('membresia', response.data)
        self.assertIn('dateInitial', response.data)
        self.assertIn('dateFinal', response.data)
        self.assertIn('price', response.data)
        
        # New assignment should have different ID
        self.assertNotEqual(response.data['id'], self.asignada.id)
        
        # dateInitial should be today (2026-08-01)
        self.assertEqual(response.data['dateInitial'], '01-08-2026')
        
        # dateFinal should be today + duration (30 days) = 2026-08-31
        self.assertEqual(response.data['dateFinal'], '31-08-2026')
        
        # Price should be the plan price
        self.assertEqual(float(response.data['price']), float(self.membresia.price))
        
        # Should have created a new assignment in DB
        new_assignment_count = MembresiaAsignada.objects.filter(miembro=self.miembro).count()
        self.assertEqual(new_assignment_count, 2)  # Original + new renewal

    def test_renovar_with_different_membership(self):
        """Renovar should allow selecting a different membership."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from gimnasioApp.models import MembresiaAsignada
        from datetime import date
        
        # Create a different membership
        membresia_nueva = create_membresia(
            self.gimnasio, name="Plan Premium", price=75000, duration=45, max_multiplier=8
        )
        
        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'membresia_id': membresia_nueva.id,
            'reason': 'Renovación a plan premium',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 8, 1))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # New assignment should have the new membership
        self.assertEqual(response.data['membresia'], membresia_nueva.id)
        self.assertEqual(response.data['membresia_details']['name'], 'Plan Premium')
        
        # dateFinal should be today + 45 days = 2026-09-15
        self.assertEqual(response.data['dateFinal'], '15-09-2026')
        
        # Price should be the new plan price
        self.assertEqual(float(response.data['price']), float(membresia_nueva.price))

    def test_renovar_with_multiplier_and_discount(self):
        """Renovar should support multiplier and discount_percent."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from gimnasioApp.models import MembresiaAsignada
        from datetime import date
        
        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'membresia_id': self.membresia.id,
            'multiplier': '2',
            'discount_percent': '10',
            'reason': 'Renovación con 2 meses y 10% descuento',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        # Override get_today to return fixed test date
        view.cls.get_today = classmethod(lambda cls: date(2026, 8, 1))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Price = 50000 * 2 * (1 - 10/100) = 100000 * 0.9 = 90000
        expected_price = 90000
        self.assertEqual(float(response.data['price']), expected_price)
        
        # dateFinal = today + 30 * 2 = 60 days = 2026-09-30
        self.assertEqual(response.data['dateFinal'], '30-09-2026')
        self.assertEqual(response.data['multiplier'], '2.0')
        self.assertEqual(response.data['discount_percent'], '10.00')

    def test_renovar_validates_max_multiplier(self):
        """Renovar should validate multiplier against selected plan's max_multiplier."""
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet
        from datetime import date
        
        # Plan has max_multiplier=12
        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'membresia_id': self.membresia.id,
            'multiplier': '15',  # Exceeds max_multiplier of 12
            'reason': 'Renovación con multiplier inválido',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        view.cls.get_today = classmethod(lambda cls: date(2026, 8, 1))
        response = view(request, pk=self.asignada.id)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            'multiplier' in str(response.data) or 'non_field_errors' in str(response.data)
        )

    def test_renovar_multi_tenant_isolation(self):
        """Renovar should only work within the same gimnasio."""
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

        view = MembresiaAsignadaViewSet.as_view({'post': 'renovar'})
        data = {
            'membresia_id': membresia2.id,
            'reason': 'Renovación en otro gimnasio',
        }
        request = self.factory.post('/', data)
        request.user = self.user  # User from gym1
        request.gimnasio = self.gimnasio  # Gym1
        force_authenticate(request, user=self.user)

        response = view(request, pk=asignada2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)