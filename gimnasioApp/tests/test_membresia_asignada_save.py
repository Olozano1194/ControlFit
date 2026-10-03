"""Tests for MembresiaAsignada.save() con multiplier y discount_percent.

Extracted from the original tests.py (lines 423-725).
"""

from django.test import TestCase
from rest_framework import status
from decimal import Decimal
from datetime import date

from .factories import (
    create_gimnasio, create_miembro, create_membresia, create_membresia_asignada
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