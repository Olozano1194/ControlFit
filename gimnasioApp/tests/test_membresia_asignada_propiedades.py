"""Tests for propiedades calculadas total_pagado, saldo_pendiente, estado_pago.

Extracted from the original tests.py.
"""

from django.test import TestCase
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_miembro, create_membresia, create_membresia_asignada
)


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