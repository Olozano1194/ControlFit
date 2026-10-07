"""Tests for OperationLog audit model.

Model-level tests for OperationLog - written first to fail (RED).
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


class OperationLogModelTest(TestCase):
    """Tests for OperationLog model."""

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

    def test_suspender_creates_log(self):
        """REQ-1: suspender success creates an OperationLog with correct fields."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet

        view = MembresiaAsignadaViewSet.as_view({'post': 'suspender'})
        data = {
            'dias': 10,
            'reason': 'Licencia médica por 10 días',
        }
        request = self.factory.post('/', data)
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        count_before = OperationLog.objects.count()

        response = view(request, pk=self.asignada.id)

        count_after = OperationLog.objects.count()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_after, count_before + 1)

        log = OperationLog.objects.latest('created_at')
        self.assertEqual(log.operation_type, 'suspender')
        self.assertEqual(log.reason, 'Licencia médica por 10 días')
        self.assertEqual(log.usuario, self.user)
        self.assertEqual(log.gimnasio, self.gimnasio)
        self.assertEqual(log.membresia_asignada, self.asignada)
        self.assertIsNotNone(log.created_at)
        self.assertIn('dias', log.details)
        self.assertIn('original_date_final', log.details)
        self.assertIn('new_date_final', log.details)

    def test_rejected_operation_no_log(self):
        """REQ-1: rejected operation (400) creates no OperationLog."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_views import MembresiaAsignadaViewSet

        view = MembresiaAsignadaViewSet.as_view({'post': 'suspender'})
        data = {
            'dias': 10,
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

        # Assignment should be unchanged
        self.asignada.refresh_from_db()
        self.assertEqual(self.asignada.dateFinal, date(2026, 7, 31))

    def test_log_operation_ignores_request_gimnasio(self):
        """BR-1: log_operation helper uses assignment's gimnasio, not request.gimnasio."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_audit import log_operation

        gym2 = create_gimnasio(name="Gym 2")
        request = self.factory.post('/')
        request.user = self.user
        request.gimnasio = gym2  # Different gym!
        force_authenticate(request, user=self.user)

        log = log_operation(
            request=request,
            asignacion=self.asignada,
            operation_type='suspender',
            reason='Test reason',
            details={'dias': 5}
        )

        self.assertEqual(log.gimnasio, self.gimnasio)
        self.assertNotEqual(log.gimnasio, gym2)


class OperationLogSuperadminTest(TestCase):
    """Tests for superadmin gimnasio resolution."""

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

    def test_superadmin_log_uses_assignment_gimnasio(self):
        """REQ-2: superadmin with no request.gimnasio logs assignment's gym."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_audit import log_operation

        superadmin = create_user(
            email="super@example.com",
            name="Super",
            lastname="Admin",
            password="password123",
            gimnasio=None,
            roles="superadmin"
        )

        request = self.factory.post('/')
        request.user = superadmin
        force_authenticate(request, user=superadmin)

        log = log_operation(
            request=request,
            asignacion=self.asignada,
            operation_type='suspender',
            reason='Superadmin action',
            details={'dias': 5}
        )

        self.assertEqual(log.gimnasio, self.gimnasio)
        self.assertEqual(log.usuario, superadmin)


class OperationLogTenantIsolationTest(TestCase):
    """Tests for tenant isolation."""

    def setUp(self):
        self.gimnasio1 = create_gimnasio(name="Gym 1")
        self.gimnasio2 = create_gimnasio(name="Gym 2")
        self.user1 = create_admin_user(self.gimnasio1)
        self.miembro1 = create_miembro("User1", "Gym1", self.gimnasio1)
        self.membresia1 = create_membresia(self.gimnasio1, name="Plan 1", price=50000, duration=30)
        self.asignada1 = create_membresia_asignada(
            self.miembro1, self.membresia1, date_initial=date(2026, 7, 1)
        )
        self.miembro2 = create_miembro("User2", "Gym2", self.gimnasio2)
        self.membresia2 = create_membresia(self.gimnasio2, name="Plan 2", price=50000, duration=30)
        self.asignada2 = create_membresia_asignada(
            self.miembro2, self.membresia2, date_initial=date(2026, 7, 1)
        )
        self.factory = APIRequestFactory()

    def test_tenant_isolation(self):
        """REQ-5: logs scoped to gimnasio - G1 query excludes G2."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_audit import log_operation

        request1 = self.factory.post('/')
        request1.user = self.user1
        request1.gimnasio = self.gimnasio1
        force_authenticate(request1, user=self.user1)

        request2 = self.factory.post('/')
        request2.user = self.user1
        request2.gimnasio = self.gimnasio2
        force_authenticate(request2, user=self.user1)

        log_operation(request1, self.asignada1, 'suspender', 'Gym 1 reason', {'dias': 5})
        log_operation(request2, self.asignada2, 'suspender', 'Gym 2 reason', {'dias': 5})

        gym1_logs = OperationLog.objects.filter(gimnasio=self.gimnasio1)
        self.assertEqual(gym1_logs.count(), 1)
        self.assertEqual(gym1_logs.first().reason, 'Gym 1 reason')

        gym2_logs = OperationLog.objects.filter(gimnasio=self.gimnasio2)
        self.assertEqual(gym2_logs.count(), 1)
        self.assertEqual(gym2_logs.first().reason, 'Gym 2 reason')

        self.assertEqual(OperationLog.objects.filter(gimnasio=self.gimnasio1).count(), 1)
        self.assertEqual(OperationLog.objects.filter(gimnasio=self.gimnasio2).count(), 1)


class OperationLogDetailsTest(TestCase):
    """Tests for details schema per operation type."""

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

    def test_details_keys_per_operation_type(self):
        """REQ-4: each operation_type has required details keys."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_audit import log_operation

        request = self.factory.post('/')
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        log1 = log_operation(request, self.asignada, 'suspender', 'reason1', {'dias': 5, 'original_date_final': '2026-07-31', 'new_date_final': '2026-08-10'})
        self.assertEqual(set(log1.details.keys()), {'dias', 'original_date_final', 'new_date_final'})

        membresia_nueva = create_membresia(self.gimnasio, name="Plan Nuevo", price=75000, duration=45)
        log2 = log_operation(request, self.asignada, 'cambiar_plan', 'reason2', {
            'membresia_anterior': self.membresia.id,
            'membresia_nueva': membresia_nueva.id,
            'credit': '26666.67',
            'final_price': '48333.33'
        })
        self.assertEqual(set(log2.details.keys()), {'membresia_anterior', 'membresia_nueva', 'credit', 'final_price'})

        log3 = log_operation(request, self.asignada, 'devolucion', 'reason3', {'monto': '10000', 'total_pagado_before': '0'})
        self.assertEqual(set(log3.details.keys()), {'monto', 'total_pagado_before'})

        log4 = log_operation(request, self.asignada, 'renovar', 'reason4', {
            'nueva_asignacion_id': 999,
            'membresia': self.membresia.id,
            'price': '50000'
        })
        self.assertEqual(set(log4.details.keys()), {'nueva_asignacion_id', 'membresia', 'price'})


class OperationLogHistoryTest(TestCase):
    """Tests for append-only history."""

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

    def test_history_append_only(self):
        """REQ-6: earlier rows unchanged, new rows appended."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_audit import log_operation

        request = self.factory.post('/')
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        log1 = log_operation(request, self.asignada, 'suspender', 'First reason', {'dias': 5})
        log1_pk = log1.pk
        log1_reason = log1.reason

        log2 = log_operation(request, self.asignada, 'suspender', 'Second reason', {'dias': 3})
        log2_pk = log2.pk

        self.assertEqual(OperationLog.objects.count(), 2)

        log1_refreshed = OperationLog.objects.get(pk=log1_pk)
        self.assertEqual(log1_refreshed.reason, log1_reason)
        self.assertEqual(log1_refreshed.operation_type, 'suspender')

        log2_refreshed = OperationLog.objects.get(pk=log2_pk)
        self.assertEqual(log2_refreshed.reason, 'Second reason')

        logs = list(OperationLog.objects.all())
        self.assertEqual(logs[0].pk, log2_pk)
        self.assertEqual(logs[1].pk, log1_pk)


class OperationLogRenovarTest(TestCase):
    """Tests for renovar logging original assignment."""

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

    def test_renovar_logs_original_assignment(self):
        """REQ-3: renovar logs ORIGINAL assignment; new id in details."""
        from gimnasioApp.models import OperationLog
        from gimnasioApp.views.membership_audit import log_operation

        request = self.factory.post('/')
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        nueva_asignacion_id = 999
        log = log_operation(
            request=request,
            asignacion=self.asignada,
            operation_type='renovar',
            reason='Renovación anual',
            details={
                'nueva_asignacion_id': nueva_asignacion_id,
                'membresia': self.membresia.id,
                'price': '50000'
            }
        )

        self.assertEqual(log.membresia_asignada, self.asignada)
        self.assertEqual(log.membresia_asignada_id, self.asignada.id)
        self.assertEqual(log.details['nueva_asignacion_id'], nueva_asignacion_id)