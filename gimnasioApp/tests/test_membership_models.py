"""Tests for membership model changes.

Extracted from the original tests.py (lines 822-1014).
"""

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from datetime import date

from .factories import (
    create_gimnasio, create_user, create_miembro,
    create_membresia, create_membresia_asignada
)


class MembresiaModelTest(TestCase):
    """Tests for Membresia model changes."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")

    # 6.1: Existing tests updated - Membresia objects now include max_multiplier
    def test_membresia_has_max_multiplier_default(self):
        """Membresia should default max_multiplier to 1."""
        # Test model default directly (not through factory which overrides)
        from gimnasioApp.models.membership_model import Membresia
        from decimal import Decimal
        m = Membresia.objects.create(
            gimnasio=self.gimnasio, name="Basico Plus", price=Decimal('100'), duration=15
        )
        self.assertEqual(m.max_multiplier, 1)

    def test_membresia_accepts_free_text_name(self):
        """Membresia.name should accept any string, not just choices."""
        m = create_membresia(
            self.gimnasio, name="Mensual $50k", price=50000, duration=30,
            max_multiplier=6
        )
        self.assertEqual(m.name, "Mensual $50k")

    # 6.3: unique_together per gym
    def test_unique_together_per_gym(self):
        """Two memberships with same name for same gym should raise IntegrityError."""
        create_membresia(
            self.gimnasio, name="UniquePlan", price=100, duration=15,
            max_multiplier=1
        )
        with self.assertRaises(IntegrityError):
            create_membresia(
                self.gimnasio, name="UniquePlan", price=200, duration=30,
                max_multiplier=1
            )

    def test_same_name_different_gyms_allowed(self):
        """Different gyms can have memberships with the same name."""
        gym2 = create_gimnasio(name="Gym 2")
        create_membresia(
            self.gimnasio, name="SameName", price=100, duration=15,
            max_multiplier=1
        )
        # Should not raise
        create_membresia(
            gym2, name="SameName", price=200, duration=30,
            max_multiplier=1
        )


class MembresiaAsignadaModelSaveTest(TestCase):
    """Tests for MembresiaAsignada.save() multiplier validation."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Test Gym")
        self.membresia = create_membresia(
            self.gimnasio, name="Limited", price=10000, duration=30,
            max_multiplier=4
        )
        self.miembro = create_miembro("Test", "Member", self.gimnasio)

    # 6.2: save() rejects multiplier > max_multiplier
    def test_save_rejects_multiplier_exceeds_max(self):
        """MembresiaAsignada.save() should raise ValidationError when multiplier > max_multiplier."""
        from gimnasioApp.models import MembresiaAsignada
        asignacion = MembresiaAsignada(
            miembro=self.miembro,
            membresia=self.membresia,
            multiplier=5,  # max_multiplier is 4
            dateInitial="2026-01-01"
        )
        with self.assertRaises(DjangoValidationError):
            asignacion.save()

    def test_save_accepts_valid_multiplier(self):
        """MembresiaAsignada.save() should accept multiplier <= max_multiplier."""
        from gimnasioApp.models import MembresiaAsignada
        asignacion = MembresiaAsignada(
            miembro=self.miembro,
            membresia=self.membresia,
            multiplier=3,  # max_multiplier is 4
            dateInitial="2026-01-01"
        )
        # Should not raise
        asignacion.save()
        self.assertEqual(asignacion.multiplier, 3)

    def test_save_calculates_price_with_multiplier(self):
        """save() should multiply price by multiplier on creation."""
        from gimnasioApp.models import MembresiaAsignada
        asignacion = MembresiaAsignada(
            miembro=self.miembro,
            membresia=self.membresia,
            multiplier=3,
            dateInitial="2026-01-01"
        )
        asignacion.save()
        expected_price = self.membresia.price * 3  # 10000 * 3 = 30000
        self.assertEqual(asignacion.price, expected_price)

    def test_save_calculates_date_final_with_multiplier(self):
        """save() should multiply duration by multiplier on creation."""
        from gimnasioApp.models import MembresiaAsignada
        from datetime import date, timedelta
        asignacion = MembresiaAsignada(
            miembro=self.miembro,
            membresia=self.membresia,
            multiplier=3,
            dateInitial="2026-01-01"
        )
        asignacion.save()
        expected_days = self.membresia.duration * 3  # 30 * 3 = 90
        expected_final = date(2026, 1, 1) + timedelta(days=expected_days)
        self.assertEqual(asignacion.dateFinal, expected_final)


class SeedDefaultMembershipsTest(TestCase):
    """Tests for post_save signal seed."""

    # 6.4: Seed creates 3 default memberships on Gimnasio creation
    def test_new_gym_gets_default_memberships(self):
        """Creating a new Gimnasio should seed 3 default memberships."""
        gym = create_gimnasio(name="New Gym")
        memberships = gym.membresias.all()
        self.assertEqual(memberships.count(), 3)

        names = [m.name for m in memberships]
        self.assertIn("Básico", names)
        self.assertIn("Premium", names)
        self.assertIn("VIP", names)

    def test_default_memberships_have_correct_durations(self):
        """Default memberships should have correct durations."""
        gym = create_gimnasio(name="Gym Durations")
        basico = gym.membresias.get(name="Básico")
        premium = gym.membresias.get(name="Premium")
        vip = gym.membresias.get(name="VIP")

        self.assertEqual(basico.duration, 15)
        self.assertEqual(basico.max_multiplier, 1)
        self.assertEqual(premium.duration, 30)
        self.assertEqual(premium.max_multiplier, 12)
        self.assertEqual(vip.duration, 45)
        self.assertEqual(vip.max_multiplier, 8)

    def test_default_memberships_have_zero_price(self):
        """Default memberships should have price=0."""
        gym = create_gimnasio(name="Zero Price Gym")
        for m in gym.membresias.all():
            self.assertEqual(m.price, 0)

    # 6.5: Seed does NOT re-seed when memberships already exist
    def test_seed_does_not_re_seed_existing_gym(self):
        """Saving an existing gym with memberships should NOT create duplicates."""
        gym = create_gimnasio(name="Gym With Memberships")

        # Count should be 3 (from seed)
        self.assertEqual(gym.membresias.count(), 3)

        # Add a custom membership
        create_membresia(
            gym, name="Custom Plan", price=500, duration=10,
            max_multiplier=1
        )

        # Save gym again
        gym.save()

        # Count should still be 4 (3 original + 1 custom, no duplicates)
        self.assertEqual(gym.membresias.count(), 4)

    def test_seed_skips_if_memberships_exist(self):
        """Signal should skip seed if gym already has memberships."""
        gym = create_gimnasio(name="Pre-seeded Gym")

        # Manually add a membership before the signal hypothetically fires
        create_membresia(
            gym, name="Pre-existing", price=300, duration=20,
            max_multiplier=1
        )

        # Delete what the signal created and save again
        gym.membresias.exclude(name="Pre-existing").delete()
        gym.save()

        # Should still only have the pre-existing one
        self.assertEqual(gym.membresias.count(), 1)