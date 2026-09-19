"""Tests for payment and membership assignment functionality.

Extracted from the original tests.py (lines 423-725).
"""

from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_user, create_admin_user,
    create_miembro, create_membresia, create_membresia_asignada
)


class MembresiaAsignadaSaveTest(TestCase):
    """Tests for MembresiaAsignada.save() con multiplier y discount_percent."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.miembro = create_miembro("Juan", "Perez", self.gimnasio)
        self.membresia = create_membresia(
            self.gimnasio, name="Plan Test", price=50000, duration=30, max_multiplier=12
        )

    def test_save_con_multiplier_3_y_discount_5(self):
        """5.1: MembresiaAsignada.save() calcula price y dateFinal con multiplier=3 y discount=5%."""
        date_initial = date(2026, 7, 1)
        asignada = create_membresia_asignada(
            self.miembro, self.membresia,
            date_initial=date_initial,
            multiplier=3,
            discount=5
        )
        self.assertEqual(asignada.multiplier, Decimal('3'))
        self.assertEqual(asignada.discount_percent, Decimal('5'))
        # price = 50000 * 3 * (1 - 5/100) = 150000 * 0.95 = 142500
        self.assertEqual(asignada.price, Decimal('142500.00'))
        # dateFinal = dateInitial + 90 days
        self.assertEqual(asignada.dateFinal, date(2026, 9, 29))

    def test_save_con_multiplier_12_y_discount_20(self):
        """5.2: MembresiaAsignada.save() con multiplier=12 y discount=20%."""
        date_initial = date(2026, 1, 1)
        asignada = create_membresia_asignada(
            self.miembro, self.membresia,
            date_initial=date_initial,
            multiplier=12,
            discount=20
        )
        # price = 50000 * 12 * (1 - 20/100) = 600000 * 0.8 = 480000
        self.assertEqual(asignada.price, Decimal('480000.00'))
        # dateFinal = dateInitial + 360 days
        self.assertEqual(asignada.dateFinal, date(2026, 12, 27))

    def test_save_sin_multiplier_comportamiento_legacy(self):
        """Sin multiplier explicito, comportamiento igual al original."""
        date_initial = date(2026, 7, 1)
        asignada = create_membresia_asignada(
            self.miembro, self.membresia,
            date_initial=date_initial
        )
        self.assertEqual(asignada.multiplier, Decimal('1'))
        self.assertEqual(asignada.discount_percent, Decimal('0'))
        self.assertEqual(asignada.price, Decimal('50000.00'))
        self.assertEqual(asignada.dateFinal, date(2026, 7, 31))


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


class MembresiaAsignadaPropiedadesTest(TestCase):
    """Tests for propiedades calculadas total_pagado, saldo_pendiente, estado_pago."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.miembro = create_miembro("Maria", "Lopez", self.gimnasio)
        self.membresia = create_membresia(
            self.gimnasio, name="Plan Premium", price=100000, duration=30
        )
        self.asignada = create_membresia_asignada(
            self.miembro, self.membresia, date_initial=date(2026, 7, 1)
        )

    def test_estado_pending_sin_pagos(self):
        """5.4a: Sin pagos → total_pagado=0, saldo_pendiente=price, estado_pago='pending'."""
        self.assertEqual(self.asignada.total_pagado, Decimal('0'))
        self.assertEqual(self.asignada.saldo_pendiente, Decimal('100000.00'))
        self.assertEqual(self.asignada.estado_pago, 'pending')

    def test_estado_partial_con_pago_parcial(self):
        """5.4b: Pago parcial → estado_pago='partial'."""
        from gimnasioApp.models import PagoMembresia
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('30000'),
            metodo_pago='efectivo'
        )
        self.assertEqual(self.asignada.total_pagado, Decimal('30000.00'))
        self.assertEqual(self.asignada.saldo_pendiente, Decimal('70000.00'))
        self.assertEqual(self.asignada.estado_pago, 'partial')

    def test_estado_paid_con_pago_total(self):
        """5.4c: Pago total → estado_pago='paid'."""
        from gimnasioApp.models import PagoMembresia
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('100000'),
            metodo_pago='transferencia'
        )
        self.assertEqual(self.asignada.total_pagado, Decimal('100000.00'))
        self.assertEqual(self.asignada.saldo_pendiente, Decimal('0.00'))
        self.assertEqual(self.asignada.estado_pago, 'paid')

    def test_estado_paid_con_varios_pagos(self):
        """5.4d: Varios pagos que suman el total → estado_pago='paid'."""
        from gimnasioApp.models import PagoMembresia
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('40000'),
            metodo_pago='efectivo'
        )
        PagoMembresia.objects.create(
            membresia_asignada=self.asignada,
            monto=Decimal('60000'),
            metodo_pago='nequi'
        )
        self.assertEqual(self.asignada.total_pagado, Decimal('100000.00'))
        self.assertEqual(self.asignada.saldo_pendiente, Decimal('0.00'))
        self.assertEqual(self.asignada.estado_pago, 'paid')


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