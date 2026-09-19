"""Integration tests for Home dashboard payment stats.

Extracted from the original tests.py (lines 727-820).
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from decimal import Decimal
from datetime import date
import json

from .factories import (
    create_gimnasio, create_user, create_admin_user,
    create_miembro, create_membresia, create_membresia_asignada
)


class HomeDashboardPagosTest(TestCase):
    """Integration tests for Home dashboard payment stats."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.user = create_admin_user(self.gimnasio)
        today = date.today()

        # Membresia basica de 30 dias
        self.membresia = create_membresia(
            self.gimnasio, name="Plan Test", price=50000, duration=30
        )

        # Miembro 1: Al dia (paid)
        miembro1 = create_miembro("Ana", "Garcia", self.gimnasio)
        m1 = create_membresia_asignada(
            miembro1, self.membresia, date_initial=today
        )
        from gimnasioApp.models import PagoMembresia
        PagoMembresia.objects.create(
            membresia_asignada=m1, monto=Decimal('50000'), metodo_pago='efectivo'
        )

        # Miembro 2: Con deuda (partial)
        miembro2 = create_miembro("Luis", "Martinez", self.gimnasio)
        m2 = create_membresia_asignada(
            miembro2, self.membresia, date_initial=today
        )
        PagoMembresia.objects.create(
            membresia_asignada=m2, monto=Decimal('30000'), metodo_pago='efectivo'
        )
        # saldo_pendiente = 50000 - 30000 = 20000

        # Miembro 3: Con deuda (pending - sin pagos)
        miembro3 = create_miembro("Pedro", "Ramirez", self.gimnasio)
        create_membresia_asignada(
            miembro3, self.membresia, date_initial=today
        )
        # saldo_pendiente = 50000

    def test_home_retorna_por_cobrar_al_dia_con_deuda(self):
        """5.6: GET /home/ retorna por_cobrar, al_dia, con_deuda correctos."""
        from gimnasioApp.views import Home
        view = Home.as_view()
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        # por_cobrar = 20000 (Miembro 2) + 50000 (Miembro 3) = 70000
        self.assertEqual(data['por_cobrar'], 70000.0)
        # al_dia = 1 (Miembro 1)
        self.assertEqual(data['al_dia'], 1)
        # con_deuda = 2 (Miembro 2 y 3)
        self.assertEqual(data['con_deuda'], 2)

    def test_home_multi_tenant_filtra_por_gimnasio(self):
        """Dashboard stats solo muestran datos del gimnasio del usuario."""
        # Crear otro gimnasio con miembros
        otro_gym = create_gimnasio(name="Otro Gym")
        otro_miembro = create_miembro("Otro", "Member", otro_gym)
        create_membresia_asignada(
            otro_miembro, self.membresia, date_initial=date.today()
        )

        from gimnasioApp.views import Home
        view = Home.as_view()
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        # Solo deberia contar los 3 miembros del gimnasio original
        self.assertEqual(data['num_miembros'], 3)
        self.assertEqual(data['por_cobrar'], 70000.0)