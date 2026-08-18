import io
import base64
import json
from django.test import TestCase
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from unittest.mock import patch, MagicMock, call

from decimal import Decimal
from datetime import datetime, timedelta, date, timezone as dt_timezone
from django.utils import timezone
from .models import Gimnasio, Usuario, UsuarioGym, Membresia, MembresiaAsignada, PagoMembresia, TipoEvento, EventoCalendario, Notification
from .middleware import GimnasioMiddleware
from .mixins import MultiTenantViewSetMixin
from .serializers import UsuarioSerializer, UsuarioGymSerializer, MembresiasSerializer, MembresiaAsignadaSerializer, PagoMembresiaSerializer, EventoCalendarioSerializer
from .views import UserViewSet, UsuarioGymViewSet, MembresiaViewSet, Home, PagoMembresiaViewSet, TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView, NotificationViewSet
from .services.notifications import NotificationManager
from .storage import SupabaseMediaStorage
from django.core.files.uploadedfile import SimpleUploadedFile


def _utc(year, month, day, hour=0, minute=0):
    """Helper: datetime naive → aware en UTC para los tests del calendario."""
    return timezone.make_aware(datetime(year, month, day, hour, minute), dt_timezone.utc)


class GimnasioMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = GimnasioMiddleware(lambda r: None)

    def test_authenticated_user_gets_gimnasio(self):
        gimnasio = Gimnasio.objects.create(name="Test Gym")
        user = Usuario.objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=gimnasio
        )
        request = self.factory.get('/')
        request.user = user
        self.middleware(request)
        self.assertEqual(request.gimnasio, gimnasio)

    def test_anonymous_user_gets_none(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.middleware(request)
        self.assertIsNone(request.gimnasio)

    def test_user_without_gimnasio_gets_none(self):
        gimnasio = Gimnasio.objects.create(name="Test Gym 2")
        # Create user with gimnasio first, then test the middleware behavior
        user = Usuario.objects.create_user(
            email="nogym@example.com",
            name="No",
            lastname="Gym",
            password="password123",
            gimnasio=gimnasio
        )

        # Now simulate user without gimnasio by manually setting request.gimnasio = None
        # The middleware sets request.gimnasio based on request.user.gimnasio
        # We need to test a user whose gimnasio is None
        # Since the DB requires gimnasio, we'll test the middleware logic directly
        request = self.factory.get('/')
        request.user = user
        # Manually set user.gimnasio to None to simulate the case
        user.gimnasio = None
        self.middleware(request)
        self.assertIsNone(request.gimnasio)


class MultiTenantViewSetMixinTest(TestCase):
    def setUp(self):
        self.gimnasio1 = Gimnasio.objects.create(name="Gym 1")
        self.gimnasio2 = Gimnasio.objects.create(name="Gym 2")

        self.user1 = Usuario.objects.create_user(
            email="user1@example.com",
            name="User",
            lastname="One",
            password="password123",
            gimnasio=self.gimnasio1
        )
        self.user2 = Usuario.objects.create_user(
            email="user2@example.com",
            name="User",
            lastname="Two",
            password="password123",
            gimnasio=self.gimnasio2
        )

        self.member1 = UsuarioGym.objects.create(
            name="Member", lastname="One",
            gimnasio=self.gimnasio1
        )
        self.member2 = UsuarioGym.objects.create(
            name="Member", lastname="Two",
            gimnasio=self.gimnasio2
        )

    def test_queryset_filtered_by_gimnasio(self):
        factory = APIRequestFactory()
        view = UsuarioGymViewSet.as_view({'get': 'list'})

        request = factory.get('/')
        request.user = self.user1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['gimnasio'], self.gimnasio1.id)

    def test_queryset_returns_empty_for_no_gimnasio(self):
        factory = APIRequestFactory()
        view = UsuarioGymViewSet.as_view({'get': 'list'})

        request = factory.get('/')
        request.user = self.user1
        request.gimnasio = None
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_membresia_viewset_filters_by_gimnasio(self):
        Membresia.objects.create(name="Plan 1", price=100, duration=30, gimnasio=self.gimnasio1)
        Membresia.objects.create(name="Plan 2", price=200, duration=30, gimnasio=self.gimnasio2)

        factory = APIRequestFactory()
        view = MembresiaViewSet.as_view({'get': 'list'})

        request = factory.get('/')
        request.user = self.user1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # gym1 has 3 defaults (Básico, Premium, VIP) + Plan 1 = 4, gym2 has Plan 2
        gym1_count = len([m for m in response.data if m['gimnasio'] == self.gimnasio1.id])
        gym2_count = len([m for m in response.data if m['gimnasio'] == self.gimnasio2.id])
        self.assertEqual(gym1_count, 4)
        self.assertEqual(gym2_count, 0)


class UserViewSetCreateTest(TestCase):
    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.admin = Usuario.objects.create_user(
            email="admin@example.com",
            name="Admin",
            lastname="User",
            password="password123",
            roles="admin",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def test_create_user_assigns_gimnasio_via_perform_create(self):
        view = UserViewSet.as_view({'post': 'create'})

        data = {
            "email": "newuser@example.com",
            "name": "New",
            "lastname": "User",
            "password": "password123",
            "roles": "recepcion"
        }
        request = self.factory.post('/', data)
        request.user = self.admin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.admin)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user = Usuario.objects.get(email="newuser@example.com")
        self.assertEqual(new_user.gimnasio, self.gimnasio)

    def test_create_user_without_perform_create_bypasses_gimnasio(self):
        # Verify that perform_create is actually being called
        # by checking the gimnasio is set correctly
        view = UserViewSet.as_view({'post': 'create'})

        data = {
            "email": "another@example.com",
            "name": "Another",
            "lastname": "User",
            "password": "password123",
        }
        request = self.factory.post('/', data)
        request.user = self.admin
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.admin)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user = Usuario.objects.get(email="another@example.com")
        self.assertEqual(new_user.gimnasio, self.gimnasio)


# ============================================================
# SUPABASE STORAGE TESTS (Phase 4)
# ============================================================

class SupabaseMediaStorageTest(TestCase):
    """Unit tests for SupabaseMediaStorage configuration."""

    def test_storage_uses_empty_location(self):
        """Storage should use '' as location (upload_to='fotos/' en el modelo maneja el path)."""
        storage = SupabaseMediaStorage()
        self.assertEqual(storage.location, '')

    def test_storage_does_not_overwrite_files(self):
        """Storage should NOT overwrite existing files (file_overwrite=False)."""
        storage = SupabaseMediaStorage()
        self.assertFalse(storage.file_overwrite)

    def test_storage_uses_public_read_acl(self):
        """Storage should use 'public-read' ACL for public URLs."""
        storage = SupabaseMediaStorage()
        self.assertEqual(storage.default_acl, 'public-read')

    @patch.dict('os.environ', {
        'AWS_S3_ENDPOINT_URL': 'https://test-project.supabase.co/storage/v1/s3',
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret',
        'AWS_STORAGE_BUCKET_NAME': 'test-bucket'
    })
    def test_storage_reads_endpoint_from_env(self):
        """Storage should read S3 endpoint from AWS_S3_ENDPOINT_URL env var."""
        from django.test.utils import override_settings
        with override_settings(
            AWS_S3_ENDPOINT_URL='https://test-project.supabase.co/storage/v1/s3',
            AWS_ACCESS_KEY_ID='test-key',
            AWS_SECRET_ACCESS_KEY='test-secret',
            AWS_STORAGE_BUCKET_NAME='test-bucket'
        ):
            storage = SupabaseMediaStorage()
            self.assertEqual(storage.endpoint_url, 'https://test-project.supabase.co/storage/v1/s3')

    @patch.dict('os.environ', {'AWS_STORAGE_BUCKET_NAME': 'custom-bucket'})
    def test_storage_uses_configured_bucket_name(self):
        """Storage should use bucket name from AWS_STORAGE_BUCKET_NAME env var."""
        from django.test.utils import override_settings
        with override_settings(AWS_STORAGE_BUCKET_NAME='custom-bucket'):
            storage = SupabaseMediaStorage()
            self.assertEqual(storage.bucket_name, 'custom-bucket')


class UsuarioSerializerAvatarTest(TestCase):
    """Unit tests for avatar update behavior in UsuarioSerializer."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def _make_uploaded_image(self, filename='test.jpg', fmt='JPEG'):
        """Generate a valid image file using Pillow."""
        from PIL import Image
        import io
        img = Image.new('RGB', (10, 10), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        return SimpleUploadedFile(
            filename,
            buffer.getvalue(),
            content_type='image/jpeg' if fmt == 'JPEG' else 'image/png'
        )

    def test_serializer_deletes_old_avatar_when_new_provided(self):
        """Scenario 4.2: When new avatar is provided, old avatar should be deleted from storage."""
        # Setup: user has existing avatar
        self.user.avatar = 'avatars/old_avatar.jpg'
        self.user.save()

        # Patch FieldFile.delete to intercept the storage deletion call
        with patch('django.db.models.fields.files.FieldFile.delete') as mock_delete:
            new_avatar = self._make_uploaded_image('new_avatar.jpg')
            serializer = UsuarioSerializer(
                instance=self.user,
                data={'avatar': new_avatar},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.update(self.user, {'avatar': new_avatar})

            # Verify old avatar was deleted from storage
            mock_delete.assert_called_once()

    def test_serializer_skips_deletion_on_first_time_upload(self):
        """Scenario 4.3: First-time upload (no existing avatar) should skip deletion gracefully."""
        # User has no avatar
        self.user.avatar = None
        self.user.save()

        with patch('django.db.models.fields.files.FieldFile.delete') as mock_delete:
            new_avatar = self._make_uploaded_image('test.jpg')
            serializer = UsuarioSerializer(
                instance=self.user,
                data={'avatar': new_avatar},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            result = serializer.update(self.user, {'avatar': new_avatar})

            # delete should NOT have been called since there was no old avatar
            mock_delete.assert_not_called()
            # The avatar should now be set (not None)
            self.assertIsNotNone(result.avatar)

    def test_serializer_skips_deletion_when_avatar_not_in_update(self):
        """Scenario 4.4: When avatar is NOT in the update data, existing avatar should NOT be deleted."""
        # Setup: user has existing avatar
        self.user.avatar = 'avatars/old_avatar.jpg'
        self.user.save()

        serializer = UsuarioSerializer(
            instance=self.user,
            data={'name': 'Updated Name'},
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        # Verify 'avatar' is not in validated_data
        self.assertNotIn('avatar', serializer.validated_data)

        # Mock storage delete to ensure it's not called
        with patch('django.db.models.fields.files.FieldFile.delete') as mock_delete:
            result = serializer.update(self.user, serializer.validated_data)
            mock_delete.assert_not_called()
            self.assertEqual(result.name, 'Updated Name')

    def test_serializer_deletes_old_avatar_using_storage(self):
        """Verify that storage.delete() is called on the old avatar name."""
        self.user.avatar = 'avatars/old_avatar.jpg'
        self.user.save()

        with patch('django.db.models.fields.files.FieldFile.delete') as mock_delete:
            new_avatar = self._make_uploaded_image('new_avatar.jpg')
            serializer = UsuarioSerializer(
                instance=self.user,
                data={'avatar': new_avatar},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.update(self.user, {'avatar': new_avatar})

            # Verify old avatar was deleted from storage
            mock_delete.assert_called_once()


# ============================================================
# INTEGRATION TESTS (Phase 4.5)
# ============================================================

class AvatarUploadIntegrationTest(TestCase):
    """Integration test for end-to-end avatar upload."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            roles="admin",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def _make_uploaded_image(self, filename='test.jpg', fmt='JPEG'):
        """Generate a valid image file using Pillow."""
        from PIL import Image
        import io
        img = Image.new('RGB', (10, 10), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        return SimpleUploadedFile(
            filename,
            buffer.getvalue(),
            content_type='image/jpeg' if fmt == 'JPEG' else 'image/png'
        )

    def test_avatar_upload_returns_url(self):
        """PATCH /api/user/ with avatar should return the avatar URL."""
        mock_storage = MagicMock()
        mock_storage.url.return_value = 'https://test-project.supabase.co/storage/v1/object/public/fotos/test.jpg'
        mock_storage.save.return_value = 'fotos/test.jpg'
        mock_storage.exists.return_value = False

        # Patch the storage used by the avatar field
        with patch.object(Usuario.avatar.field, 'storage', mock_storage):
            new_avatar = self._make_uploaded_image('test.jpg')
            view = UserViewSet.as_view({'patch': 'partial_update'})
            request = self.factory.patch('/api/user/', {'avatar': new_avatar}, format='multipart')
            request.user = self.user
            request.gimnasio = self.gimnasio
            force_authenticate(request, user=self.user)

            with patch.object(UserViewSet, 'get_object', return_value=self.user):
                response = view(request, pk=self.user.id)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # Assert response contains Supabase URL (starts with 'http')
                self.assertIn('avatar', response.data)
                avatar_url = response.data['avatar']
                self.assertTrue(avatar_url.startswith('http'), f"Avatar URL should start with 'http', got: {avatar_url}")


# ============================================================
# PHASE 5: PAGOS FLEXIBLES DE MEMBRESIAS — TESTS
# ============================================================

class MembresiaAsignadaSaveTest(TestCase):
    """Tests for MembresiaAsignada.save() con multiplier y discount_percent."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.miembro = UsuarioGym.objects.create(
            name="Juan", lastname="Perez", gimnasio=self.gimnasio
        )
        self.membresia = Membresia.objects.create(
            name="Plan Test", price=Decimal('50000'), duration=30, max_multiplier=12, gimnasio=self.gimnasio
        )

    def test_save_con_multiplier_3_y_discount_5(self):
        """5.1: MembresiaAsignada.save() calcula price y dateFinal con multiplier=3 y discount=5%."""
        date_initial = date(2026, 7, 1)
        asignada = MembresiaAsignada.objects.create(
            miembro=self.miembro,
            membresia=self.membresia,
            dateInitial=date_initial,
            multiplier=Decimal('3'),
            discount_percent=Decimal('5')
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
        asignada = MembresiaAsignada.objects.create(
            miembro=self.miembro,
            membresia=self.membresia,
            dateInitial=date_initial,
            multiplier=Decimal('12'),
            discount_percent=Decimal('20')
        )
        # price = 50000 * 12 * (1 - 20/100) = 600000 * 0.8 = 480000
        self.assertEqual(asignada.price, Decimal('480000.00'))
        # dateFinal = dateInitial + 360 days
        self.assertEqual(asignada.dateFinal, date(2026, 12, 27))

    def test_save_sin_multiplier_comportamiento_legacy(self):
        """Sin multiplier explicito, comportamiento igual al original."""
        date_initial = date(2026, 7, 1)
        asignada = MembresiaAsignada.objects.create(
            miembro=self.miembro,
            membresia=self.membresia,
            dateInitial=date_initial
        )
        self.assertEqual(asignada.multiplier, Decimal('1'))
        self.assertEqual(asignada.discount_percent, Decimal('0'))
        self.assertEqual(asignada.price, Decimal('50000.00'))
        self.assertEqual(asignada.dateFinal, date(2026, 7, 31))


class PagoMembresiaValidacionTest(TestCase):
    """Tests for PagoMembresia validacion de monto."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.miembro = UsuarioGym.objects.create(
            name="Juan", lastname="Perez", gimnasio=self.gimnasio
        )
        self.membresia = Membresia.objects.create(
            name="Plan Test", price=Decimal('100000'), duration=30, gimnasio=self.gimnasio
        )
        self.asignada = MembresiaAsignada.objects.create(
            miembro=self.miembro,
            membresia=self.membresia,
            dateInitial=date(2026, 7, 1)
        )

    def test_monto_no_excede_saldo_pendiente(self):
        """5.3: Validacion: monto no excede saldo_pendiente."""
        # saldo_pendiente = 100000
        # intentar pagar 150000 debe fallar
        pago = PagoMembresia(membresia_asignada=self.asignada, monto=Decimal('150000'), metodo_pago='efectivo')
        from django.core.exceptions import ValidationError as DjangoValidationError
        # La validacion ocurre en el serializer, no en el modelo
        # Probamos directamente que la logica funciona
        self.assertGreater(Decimal('150000'), self.asignada.saldo_pendiente)
        
        # Verificar que el serializer rechaza el sobrepago
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post('/')
        from rest_framework.test import force_authenticate
        from .models import Usuario
        user = Usuario.objects.create_user(
            email="test@test.com", name="Test", lastname="User",
            password="pass123", gimnasio=self.gimnasio
        )
        request.user = user
        request.gimnasio = self.gimnasio

        data = {
            'membresia_asignada': self.asignada.id,
            'monto': 150000,
            'metodo_pago': 'efectivo',
            'nota': ''
        }
        serializer = PagoMembresiaSerializer(
            data=data,
            context={'request': request, 'membresia_asignada': self.asignada}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('monto', serializer.errors)

    def test_monto_cero_rechazado(self):
        """Monto = 0 debe ser rechazado."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        from .models import Usuario
        factory = APIRequestFactory()
        request = factory.post('/')
        user = Usuario.objects.create_user(
            email="test2@test.com", name="Test", lastname="User",
            password="pass123", gimnasio=self.gimnasio
        )
        request.user = user
        request.gimnasio = self.gimnasio

        data = {
            'membresia_asignada': self.asignada.id,
            'monto': 0,
            'metodo_pago': 'efectivo'
        }
        serializer = PagoMembresiaSerializer(
            data=data,
            context={'request': request, 'membresia_asignada': self.asignada}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('monto', serializer.errors)

    def test_monto_negativo_rechazado(self):
        """Monto negativo debe ser rechazado."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        from .models import Usuario
        factory = APIRequestFactory()
        request = factory.post('/')
        user = Usuario.objects.create_user(
            email="test3@test.com", name="Test", lastname="User",
            password="pass123", gimnasio=self.gimnasio
        )
        request.user = user
        request.gimnasio = self.gimnasio

        data = {
            'membresia_asignada': self.asignada.id,
            'monto': -100,
            'metodo_pago': 'efectivo'
        }
        serializer = PagoMembresiaSerializer(
            data=data,
            context={'request': request, 'membresia_asignada': self.asignada}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('monto', serializer.errors)


class MembresiaAsignadaPropiedadesTest(TestCase):
    """Tests for propiedades calculadas total_pagado, saldo_pendiente, estado_pago."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.miembro = UsuarioGym.objects.create(
            name="Maria", lastname="Lopez", gimnasio=self.gimnasio
        )
        self.membresia = Membresia.objects.create(
            name="Plan Premium", price=Decimal('100000'), duration=30, gimnasio=self.gimnasio
        )
        self.asignada = MembresiaAsignada.objects.create(
            miembro=self.miembro,
            membresia=self.membresia,
            dateInitial=date(2026, 7, 1)
        )

    def test_estado_pending_sin_pagos(self):
        """5.4a: Sin pagos → total_pagado=0, saldo_pendiente=price, estado_pago='pending'."""
        self.assertEqual(self.asignada.total_pagado, Decimal('0'))
        self.assertEqual(self.asignada.saldo_pendiente, Decimal('100000.00'))
        self.assertEqual(self.asignada.estado_pago, 'pending')

    def test_estado_partial_con_pago_parcial(self):
        """5.4b: Pago parcial → estado_pago='partial'."""
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
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.objects.create_user(
            email="admin@gym.com", name="Admin", lastname="User",
            password="pass123", roles="admin", gimnasio=self.gimnasio
        )
        self.miembro = UsuarioGym.objects.create(
            name="Carlos", lastname="Mendez", gimnasio=self.gimnasio
        )
        self.membresia = Membresia.objects.create(
            name="Plan Test", price=Decimal('50000'), duration=30, gimnasio=self.gimnasio
        )
        self.asignada = MembresiaAsignada.objects.create(
            miembro=self.miembro,
            membresia=self.membresia,
            dateInitial=date(2026, 7, 1)
        )
        self.factory = APIRequestFactory()

    def test_post_pago_registra_abono(self):
        """5.5: POST pago registra abono y actualiza estado."""
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

        view = PagoMembresiaViewSet.as_view({'get': 'list'})
        request = self.factory.get('/')
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)

        response = view(request, pk=self.asignada.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by fecha_pago descending
        self.assertEqual(len(response.data), 2)


class HomeDashboardPagosTest(TestCase):
    """Integration tests for Home dashboard payment stats."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.objects.create_user(
            email="admin@gym.com", name="Admin", lastname="User",
            password="pass123", roles="admin", gimnasio=self.gimnasio
        )
        today = date.today()

        # Membresia basica de 30 dias
        self.membresia = Membresia.objects.create(
            name="Plan Test", price=Decimal('50000'), duration=30, gimnasio=self.gimnasio
        )

        # Miembro 1: Al dia (paid)
        miembro1 = UsuarioGym.objects.create(name="Ana", lastname="Garcia", gimnasio=self.gimnasio)
        m1 = MembresiaAsignada.objects.create(
            miembro=miembro1, membresia=self.membresia,
            dateInitial=today
        )
        PagoMembresia.objects.create(
            membresia_asignada=m1, monto=Decimal('50000'), metodo_pago='efectivo'
        )

        # Miembro 2: Con deuda (partial)
        miembro2 = UsuarioGym.objects.create(name="Luis", lastname="Martinez", gimnasio=self.gimnasio)
        m2 = MembresiaAsignada.objects.create(
            miembro=miembro2, membresia=self.membresia,
            dateInitial=today
        )
        PagoMembresia.objects.create(
            membresia_asignada=m2, monto=Decimal('30000'), metodo_pago='efectivo'
        )
        # saldo_pendiente = 50000 - 30000 = 20000

        # Miembro 3: Con deuda (pending - sin pagos)
        miembro3 = UsuarioGym.objects.create(name="Pedro", lastname="Ramirez", gimnasio=self.gimnasio)
        MembresiaAsignada.objects.create(
            miembro=miembro3, membresia=self.membresia,
            dateInitial=today
        )
        # saldo_pendiente = 50000

    def test_home_retorna_por_cobrar_al_dia_con_deuda(self):
        """5.6: GET /home/ retorna por_cobrar, al_dia, con_deuda correctos."""
        view = Home.as_view()
        from rest_framework.test import APIRequestFactory
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
        otro_gym = Gimnasio.objects.create(name="Otro Gym")
        otro_miembro = UsuarioGym.objects.create(name="Otro", lastname="Member", gimnasio=otro_gym)
        MembresiaAsignada.objects.create(
            miembro=otro_miembro, membresia=self.membresia,
            dateInitial=date.today()
        )

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


# ============================================================
# PHASE 6: CUSTOMIZABLE MEMBERSHIPS TESTS
# ============================================================

class MembresiaModelTest(TestCase):
    """Tests for Membresia model changes."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        # Note: seed signal creates Básico/Premium/VIP automatically
        self.membresia = Membresia.objects.create(
            name="Premium Pro",
            price=50000,
            duration=30,
            max_multiplier=12,
            gimnasio=self.gimnasio
        )

    # 6.1: Existing tests updated - Membresia objects now include max_multiplier
    def test_membresia_has_max_multiplier_default(self):
        """Membresia should default max_multiplier to 1."""
        m = Membresia.objects.create(
            name="Basico Plus", price=100, duration=15, gimnasio=self.gimnasio
        )
        self.assertEqual(m.max_multiplier, 1)

    def test_membresia_accepts_free_text_name(self):
        """Membresia.name should accept any string, not just choices."""
        m = Membresia.objects.create(
            name="Mensual $50k", price=50000, duration=30,
            max_multiplier=6, gimnasio=self.gimnasio
        )
        self.assertEqual(m.name, "Mensual $50k")

    # 6.3: unique_together per gym
    def test_unique_together_per_gym(self):
        """Two memberships with same name for same gym should raise IntegrityError."""
        Membresia.objects.create(
            name="UniquePlan", price=100, duration=15,
            max_multiplier=1, gimnasio=self.gimnasio
        )
        with self.assertRaises(IntegrityError):
            Membresia.objects.create(
                name="UniquePlan", price=200, duration=30,
                max_multiplier=1, gimnasio=self.gimnasio
            )

    def test_same_name_different_gyms_allowed(self):
        """Different gyms can have memberships with the same name."""
        gym2 = Gimnasio.objects.create(name="Gym 2")
        Membresia.objects.create(
            name="SameName", price=100, duration=15,
            max_multiplier=1, gimnasio=self.gimnasio
        )
        # Should not raise
        Membresia.objects.create(
            name="SameName", price=200, duration=30,
            max_multiplier=1, gimnasio=gym2
        )


class MembresiaAsignadaModelSaveTest(TestCase):
    """Tests for MembresiaAsignada.save() multiplier validation."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.membresia = Membresia.objects.create(
            name="Limited", price=10000, duration=30,
            max_multiplier=4, gimnasio=self.gimnasio
        )
        self.miembro = UsuarioGym.objects.create(
            name="Test", lastname="Member", gimnasio=self.gimnasio
        )

    # 6.2: save() rejects multiplier > max_multiplier
    def test_save_rejects_multiplier_exceeds_max(self):
        """MembresiaAsignada.save() should raise ValidationError when multiplier > max_multiplier."""
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
        gym = Gimnasio.objects.create(name="New Gym")
        memberships = Membresia.objects.filter(gimnasio=gym)
        self.assertEqual(memberships.count(), 3)

        names = [m.name for m in memberships]
        self.assertIn("Básico", names)
        self.assertIn("Premium", names)
        self.assertIn("VIP", names)

    def test_default_memberships_have_correct_durations(self):
        """Default memberships should have correct durations."""
        gym = Gimnasio.objects.create(name="Gym Durations")
        basico = Membresia.objects.get(gimnasio=gym, name="Básico")
        premium = Membresia.objects.get(gimnasio=gym, name="Premium")
        vip = Membresia.objects.get(gimnasio=gym, name="VIP")

        self.assertEqual(basico.duration, 15)
        self.assertEqual(basico.max_multiplier, 1)
        self.assertEqual(premium.duration, 30)
        self.assertEqual(premium.max_multiplier, 12)
        self.assertEqual(vip.duration, 45)
        self.assertEqual(vip.max_multiplier, 8)

    def test_default_memberships_have_zero_price(self):
        """Default memberships should have price=0."""
        gym = Gimnasio.objects.create(name="Zero Price Gym")
        for m in Membresia.objects.filter(gimnasio=gym):
            self.assertEqual(m.price, 0)

    # 6.5: Seed does NOT re-seed when memberships already exist
    def test_seed_does_not_re_seed_existing_gym(self):
        """Saving an existing gym with memberships should NOT create duplicates."""
        gym = Gimnasio.objects.create(name="Gym With Memberships")

        # Count should be 3 (from seed)
        self.assertEqual(Membresia.objects.filter(gimnasio=gym).count(), 3)

        # Add a custom membership
        Membresia.objects.create(
            name="Custom Plan", price=500, duration=10,
            max_multiplier=1, gimnasio=gym
        )

        # Save gym again
        gym.save()

        # Count should still be 4 (3 original + 1 custom, no duplicates)
        self.assertEqual(Membresia.objects.filter(gimnasio=gym).count(), 4)

    def test_seed_skips_if_memberships_exist(self):
        """Signal should skip seed if gym already has memberships."""
        gym = Gimnasio.objects.create(name="Pre-seeded Gym")

        # Manually add a membership before the signal hypothetically fires
        Membresia.objects.create(
            name="Pre-existing", price=300, duration=20,
            max_multiplier=1, gimnasio=gym
        )

        # Delete what the signal created and save again
        Membresia.objects.filter(gimnasio=gym).exclude(name="Pre-existing").delete()
        gym.save()

        # Should still only have the pre-existing one
        self.assertEqual(Membresia.objects.filter(gimnasio=gym).count(), 1)


class MembresiasSerializerTest(TestCase):
    """Tests for MembresiasSerializer."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")

    # 6.6: MembresiasSerializer rejects duration=0 or duration=400
    def test_rejects_duration_zero(self):
        """Serializer should reject duration=0."""
        data = {
            "name": "Test Plan",
            "price": 100,
            "duration": 0,
            "max_multiplier": 1
        }
        serializer = MembresiasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("duration", serializer.errors)

    def test_rejects_duration_above_365(self):
        """Serializer should reject duration=400."""
        data = {
            "name": "Test Plan",
            "price": 100,
            "duration": 400,
            "max_multiplier": 1
        }
        serializer = MembresiasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("duration", serializer.errors)

    def test_accepts_valid_duration(self):
        """Serializer should accept duration=30."""
        data = {
            "name": "Test Plan",
            "price": 100,
            "duration": 30,
            "max_multiplier": 1
        }
        serializer = MembresiasSerializer(data=data, context={'request': self._make_request()})
        # Without gimnasio in context, create will fail, but validation should pass
        self.assertTrue(serializer.is_valid())

    def test_accepts_valid_duration_edge(self):
        """Serializer should accept duration=1 and duration=365."""
        for dur in [1, 365]:
            data = {
                "name": f"Plan {dur}",
                "price": 100,
                "duration": dur,
                "max_multiplier": 1
            }
            serializer = MembresiasSerializer(data=data, context={'request': self._make_request()})
            self.assertTrue(serializer.is_valid(), f"Duration {dur} should be valid")

    def _make_request(self):
        """Create a mock request with gimnasio."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.gimnasio = self.gimnasio
        return request


class MembresiaAsignadaSerializerValidationTest(TestCase):
    """Tests for MembresiaAsignadaSerializer multiplier validation."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.membresia = Membresia.objects.create(
            name="Limited", price=10000, duration=30,
            max_multiplier=4, gimnasio=self.gimnasio
        )
        self.miembro = UsuarioGym.objects.create(
            name="Test", lastname="Member", gimnasio=self.gimnasio
        )

    # 6.7: MembresiaAsignadaSerializer rejects multiplier > max_multiplier
    def test_serializer_rejects_multiplier_exceeds_max(self):
        """Serializer should reject multiplier > max_multiplier."""
        data = {
            "miembro": self.miembro.id,
            "membresia": self.membresia.id,
            "multiplier": 5,  # max is 4
            "dateInitial": "2026-01-01"
        }
        serializer = MembresiaAsignadaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_serializer_accepts_valid_multiplier(self):
        """Serializer should accept multiplier <= max_multiplier."""
        from datetime import date, timedelta
        data = {
            "miembro": self.miembro.id,
            "membresia": self.membresia.id,
            "multiplier": 3,  # max is 4
            "dateInitial": (date.today() + timedelta(days=365)).isoformat()
        }
        serializer = MembresiaAsignadaSerializer(data=data, context={'request': self._make_request()})
        self.assertTrue(serializer.is_valid(), f"Errors: {serializer.errors}")

    def _make_request(self):
        """Create a mock request with gimnasio."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.gimnasio = self.gimnasio
        return request


# ============================================================
# CALENDARIO BACKEND — TESTS (TipoEvento + EventoCalendario + Public Endpoint)
# ============================================================

class TipoEventoModelTest(TestCase):
    """Tests del modelo TipoEvento."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Gym Model")

    def test_create_tipo_evento_sets_fields(self):
        tipo = TipoEvento.objects.create(
            nombre="Clase", color="#FF0000", gimnasio=self.gimnasio
        )
        self.assertEqual(tipo.nombre, "Clase")
        self.assertEqual(tipo.color, "#FF0000")
        self.assertEqual(tipo.gimnasio, self.gimnasio)
        self.assertIsNotNone(tipo.created_at)

    def test_ordering_by_nombre(self):
        TipoEvento.objects.create(nombre="Zumba", color="#00FF00", gimnasio=self.gimnasio)
        TipoEvento.objects.create(nombre="Clase", color="#FF0000", gimnasio=self.gimnasio)
        tipos = list(TipoEvento.objects.filter(gimnasio=self.gimnasio))
        self.assertEqual([t.nombre for t in tipos], ["Clase", "Zumba"])

    def test_tipo_evento_isolated_by_gimnasio(self):
        gym2 = Gimnasio.objects.create(name="Gym 2")
        TipoEvento.objects.create(nombre="A", color="#000000", gimnasio=self.gimnasio)
        TipoEvento.objects.create(nombre="B", color="#111111", gimnasio=gym2)
        self.assertEqual(TipoEvento.objects.filter(gimnasio=self.gimnasio).count(), 1)
        self.assertEqual(TipoEvento.objects.filter(gimnasio=gym2).count(), 1)


class EventoCalendarioModelTest(TestCase):
    """Tests del modelo EventoCalendario."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Gym Model")
        self.tipo = TipoEvento.objects.create(
            nombre="Clase", color="#FF0000", gimnasio=self.gimnasio
        )
        self.user = Usuario.objects.create_user(
            email="cal-model@example.com", name="Cal", lastname="Model",
            password="password123", roles="admin", gimnasio=self.gimnasio
        )

    def test_create_evento_with_tipo_and_created_by(self):
        evento = EventoCalendario.objects.create(
            titulo="Yoga",
            fecha_inicio=_utc(2026, 8, 15, 10, 0),
            fecha_fin=_utc(2026, 8, 15, 12, 0),
            tipo=self.tipo,
            created_by=self.user,
            gimnasio=self.gimnasio,
        )
        self.assertEqual(evento.titulo, "Yoga")
        self.assertEqual(evento.tipo, self.tipo)
        self.assertEqual(evento.created_by, self.user)
        self.assertEqual(evento.descripcion, "")
        self.assertIsNone(evento.relacion_id)

    def test_create_evento_with_null_optionals(self):
        evento = EventoCalendario.objects.create(
            titulo="Reunión",
            fecha_inicio=_utc(2026, 8, 16, 9, 0),
            fecha_fin=_utc(2026, 8, 16, 10, 0),
            tipo=None, relacion_tipo=None, relacion_id=None, created_by=None,
            gimnasio=self.gimnasio,
        )
        self.assertIsNone(evento.tipo)
        self.assertIsNone(evento.relacion_tipo)
        self.assertIsNone(evento.relacion_id)
        self.assertIsNone(evento.created_by)


class TipoEventoViewSetTest(TestCase):
    """Tests del viewset TipoEvento: CRUD admin-only y aislamiento multi-tenant."""

    def setUp(self):
        self.gimnasio1 = Gimnasio.objects.create(name="Gym 1")
        self.gimnasio2 = Gimnasio.objects.create(name="Gym 2")
        self.admin1 = Usuario.objects.create_user(
            email="admin1@example.com", name="A", lastname="One",
            password="password123", roles="admin", gimnasio=self.gimnasio1
        )
        self.admin2 = Usuario.objects.create_user(
            email="admin2@example.com", name="A", lastname="Two",
            password="password123", roles="admin", gimnasio=self.gimnasio2
        )
        self.recepcion1 = Usuario.objects.create_user(
            email="rec1@example.com", name="R", lastname="One",
            password="password123", roles="recepcion", gimnasio=self.gimnasio1
        )
        self.factory = APIRequestFactory()

    def test_admin_creates_tipo_evento(self):
        view = TipoEventoViewSet.as_view({'post': 'create'})
        request = self.factory.post('/', {'nombre': 'Clase', 'color': '#FF0000'}, format='json')
        request.user = self.admin1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.admin1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Clase')
        self.assertEqual(response.data['color'], '#FF0000')
        self.assertEqual(response.data['gimnasio'], self.gimnasio1.id)
        tipo = TipoEvento.objects.get(id=response.data['id'])
        self.assertEqual(tipo.gimnasio, self.gimnasio1)

    def test_recepcion_user_cannot_create(self):
        view = TipoEventoViewSet.as_view({'post': 'create'})
        request = self.factory.post('/', {'nombre': 'Clase', 'color': '#FF0000'}, format='json')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_only_own_gym_types(self):
        for i in range(3):
            TipoEvento.objects.create(nombre=f"Tipo G1 {i}", color="#000000", gimnasio=self.gimnasio1)
        for i in range(2):
            TipoEvento.objects.create(nombre=f"Tipo G2 {i}", color="#111111", gimnasio=self.gimnasio2)
        view = TipoEventoViewSet.as_view({'get': 'list'})
        request = self.factory.get('/')
        request.user = self.admin1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.admin1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertTrue(all(item['gimnasio'] == self.gimnasio1.id for item in response.data))

    def test_update_scoped_to_own_gym_returns_404(self):
        tipo_g1 = TipoEvento.objects.create(nombre="G1 Only", color="#000000", gimnasio=self.gimnasio1)
        view = TipoEventoViewSet.as_view({'put': 'update'})
        request = self.factory.put('/', {'nombre': 'Hacked', 'color': '#FFFFFF'}, format='json')
        request.user = self.admin2
        request.gimnasio = self.gimnasio2
        force_authenticate(request, user=self.admin2)
        response = view(request, pk=tipo_g1.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_removes_tipo(self):
        tipo = TipoEvento.objects.create(nombre="Delete Me", color="#000000", gimnasio=self.gimnasio1)
        view = TipoEventoViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete('/')
        request.user = self.admin1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.admin1)
        response = view(request, pk=tipo.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TipoEvento.objects.filter(id=tipo.id).exists())

    def test_missing_required_fields_returns_400(self):
        view = TipoEventoViewSet.as_view({'post': 'create'})
        request = self.factory.post('/', {'nombre': 'Clase'}, format='json')
        request.user = self.admin1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.admin1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('color', response.data)


class EventoCalendarioViewSetTest(TestCase):
    """Tests del viewset EventoCalendario: CRUD, created_by, tipo_detalle, nulos."""

    def setUp(self):
        self.gimnasio1 = Gimnasio.objects.create(name="Gym 1")
        self.gimnasio2 = Gimnasio.objects.create(name="Gym 2")
        self.recepcion1 = Usuario.objects.create_user(
            email="rec1@example.com", name="R", lastname="One",
            password="password123", roles="recepcion", gimnasio=self.gimnasio1
        )
        self.user2 = Usuario.objects.create_user(
            email="user2@example.com", name="U", lastname="Two",
            password="password123", roles="admin", gimnasio=self.gimnasio2
        )
        self.tipo = TipoEvento.objects.create(
            nombre="Clase", color="#FF0000", gimnasio=self.gimnasio1
        )
        self.factory = APIRequestFactory()

    def test_recepcion_creates_evento_sets_gimnasio_and_created_by(self):
        view = EventoCalendarioViewSet.as_view({'post': 'create'})
        data = {
            'titulo': 'Yoga',
            'fecha_inicio': '2026-08-15T10:00:00Z',
            'fecha_fin': '2026-08-15T12:00:00Z',
            'tipo': self.tipo.id,
        }
        request = self.factory.post('/', data, format='json')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evento = EventoCalendario.objects.get(id=response.data['id'])
        self.assertEqual(evento.gimnasio, self.gimnasio1)
        self.assertEqual(evento.created_by, self.recepcion1)
        self.assertEqual(evento.tipo, self.tipo)

    def test_unauthenticated_access_rejected(self):
        view = EventoCalendarioViewSet.as_view({'get': 'list'})
        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tipo_detalle_nested_when_tipo_linked(self):
        evento = EventoCalendario.objects.create(
            titulo="Yoga", fecha_inicio=_utc(2026, 8, 15, 10, 0),
            fecha_fin=_utc(2026, 8, 15, 12, 0), tipo=self.tipo, gimnasio=self.gimnasio1
        )
        serializer = EventoCalendarioSerializer(evento)
        self.assertEqual(
            serializer.data['tipo_detalle'],
            {'id': self.tipo.id, 'nombre': 'Clase', 'color': '#FF0000'}
        )
        view = EventoCalendarioViewSet.as_view({'get': 'retrieve'})
        request = self.factory.get('/')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request, pk=evento.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tipo_detalle']['nombre'], 'Clase')
        self.assertEqual(response.data['tipo_detalle']['color'], '#FF0000')

    def test_tipo_detalle_null_when_tipo_null(self):
        evento = EventoCalendario.objects.create(
            titulo="Sin Tipo", fecha_inicio=_utc(2026, 8, 15, 10, 0),
            fecha_fin=_utc(2026, 8, 15, 12, 0), tipo=None, gimnasio=self.gimnasio1
        )
        serializer = EventoCalendarioSerializer(evento)
        self.assertIsNone(serializer.data['tipo_detalle'])

    def test_create_with_optional_fields_null(self):
        view = EventoCalendarioViewSet.as_view({'post': 'create'})
        data = {
            'titulo': 'Reunión',
            'fecha_inicio': '2026-08-16T09:00:00Z',
            'fecha_fin': '2026-08-16T10:00:00Z',
            'tipo': None,
            'relacion_tipo': None,
            'relacion_id': None,
        }
        request = self.factory.post('/', data, format='json')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evento = EventoCalendario.objects.get(id=response.data['id'])
        self.assertIsNone(evento.tipo)
        self.assertIsNone(evento.relacion_tipo)
        self.assertIsNone(evento.relacion_id)

    def test_invalid_datetime_returns_400(self):
        view = EventoCalendarioViewSet.as_view({'post': 'create'})
        data = {
            'titulo': 'Bad',
            'fecha_inicio': 'not-a-date',
            'fecha_fin': '2026-08-15T12:00:00Z',
        }
        request = self.factory.post('/', data, format='json')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_inicio', response.data)

    def test_fecha_fin_before_inicio_returns_400(self):
        view = EventoCalendarioViewSet.as_view({'post': 'create'})
        data = {
            'titulo': 'Inverted',
            'fecha_inicio': '2026-08-15T12:00:00Z',
            'fecha_fin': '2026-08-15T10:00:00Z',
        }
        request = self.factory.post('/', data, format='json')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_list_scoped_to_caller_gym(self):
        for i in range(3):
            EventoCalendario.objects.create(
                titulo=f"E1-{i}", fecha_inicio=_utc(2026, 8, 15, 8, 0),
                fecha_fin=_utc(2026, 8, 15, 9, 0), gimnasio=self.gimnasio1
            )
        for i in range(2):
            EventoCalendario.objects.create(
                titulo=f"E2-{i}", fecha_inicio=_utc(2026, 8, 15, 8, 0),
                fecha_fin=_utc(2026, 8, 15, 9, 0), gimnasio=self.gimnasio2
            )
        view = EventoCalendarioViewSet.as_view({'get': 'list'})
        request = self.factory.get('/')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_partial_update_without_descripcion_keeps_existing_value(self):
        evento = EventoCalendario.objects.create(
            titulo='Original', descripcion='keep me',
            fecha_inicio=_utc(2026, 8, 15, 8, 0),
            fecha_fin=_utc(2026, 8, 15, 9, 0), gimnasio=self.gimnasio1
        )
        view = EventoCalendarioViewSet.as_view({'patch': 'partial_update'})
        request = self.factory.patch('/', {'titulo': 'Renamed'}, format='json')
        request.user = self.recepcion1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.recepcion1)
        response = view(request, pk=evento.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        evento.refresh_from_db()
        self.assertEqual(evento.titulo, 'Renamed')
        self.assertEqual(evento.descripcion, 'keep me')


class RangeFilterTest(TestCase):
    """Tests del filtro de rango con semántica de overlap (?start=&end=)."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Gym 1")
        self.user = Usuario.objects.create_user(
            email="rec@example.com", name="R", lastname="One",
            password="password123", roles="recepcion", gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()
        # E3: 07:00-09:00 ; E1: 08:00-10:00 ; E2: 09:00-11:00
        self.e3 = EventoCalendario.objects.create(
            titulo="E3", fecha_inicio=_utc(2026, 8, 15, 7, 0),
            fecha_fin=_utc(2026, 8, 15, 9, 0), gimnasio=self.gimnasio
        )
        self.e1 = EventoCalendario.objects.create(
            titulo="E1", fecha_inicio=_utc(2026, 8, 15, 8, 0),
            fecha_fin=_utc(2026, 8, 15, 10, 0), gimnasio=self.gimnasio
        )
        self.e2 = EventoCalendario.objects.create(
            titulo="E2", fecha_inicio=_utc(2026, 8, 15, 9, 0),
            fecha_fin=_utc(2026, 8, 15, 11, 0), gimnasio=self.gimnasio
        )

    def _list(self, params=None):
        view = EventoCalendarioViewSet.as_view({'get': 'list'})
        request = self.factory.get('/', params or {})
        request.user = self.user
        request.gimnasio = self.gimnasio
        force_authenticate(request, user=self.user)
        return view(request)

    def test_filter_returns_overlapping_events(self):
        response = self._list({'start': '2026-08-15T09:30:00Z', 'end': '2026-08-15T10:30:00Z'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data}
        self.assertEqual(ids, {self.e1.id, self.e2.id})

    def test_filter_excludes_non_overlapping(self):
        response = self._list({'start': '2026-08-15T10:00:00Z', 'end': '2026-08-15T12:00:00Z'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data}
        self.assertNotIn(self.e3.id, ids)
        self.assertIn(self.e1.id, ids)
        self.assertIn(self.e2.id, ids)

    def test_no_filter_returns_all_ordered_by_fecha_inicio(self):
        response = self._list()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual([item['titulo'] for item in response.data], ['E3', 'E1', 'E2'])


class PublicCalendarioEndpointTest(TestCase):
    """Tests del endpoint público GET /api/calendario/publico/{gimnasio_id}/."""

    def setUp(self):
        self.gimnasio1 = Gimnasio.objects.create(name="Gym 1")
        self.gimnasio2 = Gimnasio.objects.create(name="Gym 2")
        self.tipo = TipoEvento.objects.create(
            nombre="Clase", color="#FF0000", gimnasio=self.gimnasio1
        )

    def test_valid_gym_returns_events_ordered_with_tipo_detalle(self):
        EventoCalendario.objects.create(
            titulo="A", fecha_inicio=_utc(2026, 8, 15, 8, 0),
            fecha_fin=_utc(2026, 8, 15, 9, 0), gimnasio=self.gimnasio1
        )
        EventoCalendario.objects.create(
            titulo="B", fecha_inicio=_utc(2026, 8, 15, 7, 0),
            fecha_fin=_utc(2026, 8, 15, 8, 0), tipo=self.tipo, gimnasio=self.gimnasio1
        )
        EventoCalendario.objects.create(
            titulo="Other", fecha_inicio=_utc(2026, 8, 15, 9, 0),
            fecha_fin=_utc(2026, 8, 15, 10, 0), gimnasio=self.gimnasio2
        )
        response = self.client.get(f'/api/calendario/publico/{self.gimnasio1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual([e['titulo'] for e in data], ['B', 'A'])
        self.assertEqual(
            data[0]['tipo_detalle'],
            {'id': self.tipo.id, 'nombre': 'Clase', 'color': '#FF0000'}
        )
        self.assertIsNone(data[1]['tipo_detalle'])

    def test_unknown_gym_returns_404(self):
        response = self.client.get('/api/calendario/publico/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_returns_405(self):
        response = self.client.post(f'/api/calendario/publico/{self.gimnasio1.id}/', {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_gym_with_no_events_returns_empty_list(self):
        response = self.client.get(f'/api/calendario/publico/{self.gimnasio2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_public_endpoint_registered_outside_gym_api_v1(self):
        from django.urls import resolve
        match = resolve(f'/api/calendario/publico/{self.gimnasio1.id}/')
        self.assertEqual(match.func.cls.__name__, 'PublicCalendarioView')
        self.assertFalse(match.route.startswith('gym/api/v1'))


# ============================================================
# NOTIFICACIONES NIVEL 1 — TESTS
# ============================================================

class NotificationModelTest(TestCase):
    """Tests del modelo Notification: constraint de idempotencia y defaults."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Gym Notif")

    def _crear(self, **kwargs):
        """Helper: crea una Notification con defaults mínimos."""
        defaults = {
            'gimnasio': self.gimnasio,
            'tipo': 'por_vencer',
            'titulo': 'Título',
            'mensaje': 'Mensaje',
            'fecha': date.today(),
            'relacion_tipo': 'membership',
            'relacion_id': 100,
            'link': '/dashboard/asignar-membresia-list',
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    def test_duplicado_misma_clave_raise_integrity_error(self):
        """Escenario spec: mismo gimnasio, relacion_tipo, relacion_id y tipo → IntegrityError."""
        self._crear()
        with self.assertRaises(IntegrityError):
            self._crear()

    def test_tipo_distinto_permite_mismo_origen(self):
        """Escenario spec: mismo origen pero tipo distinto → la creación es exitosa."""
        self._crear()
        self._crear(tipo='vencida')  # No debe lanzar
        self.assertEqual(Notification.objects.count(), 2)

    def test_defaults_del_modelo(self):
        """Campos opcionales: is_read=False, read_at=None, whatsapp_link=None."""
        n = self._crear()
        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)
        self.assertIsNone(n.whatsapp_link)
        self.assertIsNotNone(n.created_at)
        self.assertEqual(n._meta.db_table, 'notification')


class NotificationManagerTest(TestCase):
    """Tests de NotificationManager.generate_for_gimnasio(): generación idempotente."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Gym Manager")
        self.miembro = UsuarioGym.objects.create(
            name="Ana", lastname="Garcia", phone="3001234567", gimnasio=self.gimnasio
        )
        self.membresia = Membresia.objects.create(
            name="Plan 30", price=Decimal('50000'), duration=30, gimnasio=self.gimnasio
        )

    def _membresia_con_fin(self, dias):
        """Crea una MembresiaAsignada cuyo dateFinal cae dentro de N días desde hoy."""
        return MembresiaAsignada.objects.create(
            miembro=self.miembro,
            membresia=self.membresia,
            dateInitial=date.today() + timedelta(days=dias - 30)
        )

    def test_genera_por_vencer_para_membresia_proxima(self):
        """Escenario spec: membresía con dateFinal en (hoy, hoy+3] → tipo='por_vencer'."""
        ma = self._membresia_con_fin(2)
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        notif = Notification.objects.get(relacion_tipo='membership', relacion_id=ma.id)
        self.assertEqual(notif.tipo, 'por_vencer')
        self.assertEqual(notif.gimnasio, self.gimnasio)
        self.assertEqual(notif.link, '/dashboard/asignar-membresia-list')
        self.assertEqual(notif.fecha, ma.dateFinal)

    def test_genera_vencida_para_membresia_vencida(self):
        """Escenario spec: membresía con dateFinal hoy o antes → tipo='vencida'."""
        ma = self._membresia_con_fin(0)
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        notif = Notification.objects.get(relacion_tipo='membership', relacion_id=ma.id)
        self.assertEqual(notif.tipo, 'vencida')

    def test_genera_evento_para_evento_de_hoy(self):
        """Escenario spec: EventoCalendario con fecha_inicio hoy → tipo='evento' con deep link."""
        evento = EventoCalendario.objects.create(
            titulo="Clase hoy",
            fecha_inicio=_utc(date.today().year, date.today().month, date.today().day, 10, 0),
            fecha_fin=_utc(date.today().year, date.today().month, date.today().day, 11, 0),
            gimnasio=self.gimnasio,
        )
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        notif = Notification.objects.get(relacion_tipo='evento', relacion_id=evento.id)
        self.assertEqual(notif.tipo, 'evento')
        self.assertIn(f'?evento={evento.id}', notif.link)

    def test_generacion_idempotente_no_duplica(self):
        """Escenario spec: segunda llamada a generate → get_or_create devuelve lo existente."""
        self._membresia_con_fin(2)
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        total_primera = Notification.objects.count()
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        self.assertEqual(Notification.objects.count(), total_primera)

    def test_miembro_sin_telefono_no_genera_whatsapp_link(self):
        """Edge case: miembro sin phone → whatsapp_link=None."""
        sin_phone = UsuarioGym.objects.create(
            name="Solo", lastname="Numero", phone="", gimnasio=self.gimnasio
        )
        MembresiaAsignada.objects.create(
            miembro=sin_phone, membresia=self.membresia,
            dateInitial=date.today() - timedelta(days=31)
        )
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        notif = Notification.objects.get(relacion_tipo='membership', relacion_id__isnull=False, tipo='vencida')
        self.assertIsNone(notif.whatsapp_link)

    def test_miembro_con_telefono_genera_whatsapp_link_con_prefijo_57(self):
        """Escenario spec: whatsapp_link incluye el teléfono con prefijo 57."""
        ma = self._membresia_con_fin(1)
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        notif = Notification.objects.get(relacion_tipo='membership', relacion_id=ma.id)
        self.assertIsNotNone(notif.whatsapp_link)
        self.assertTrue(notif.whatsapp_link.startswith('https://wa.me/57'))

    def test_frontera_media_noche_datefinal_hoy_es_vencida(self):
        """Edge case límite: dateFinal == hoy → vencida (no por_vencer)."""
        ma = self._membresia_con_fin(0)
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        notif = Notification.objects.get(relacion_tipo='membership', relacion_id=ma.id)
        self.assertEqual(notif.tipo, 'vencida')

    def test_frontera_hoy_mas_3_es_por_vencer_y_mas_4_no_genera(self):
        """Edge case límite: dateFinal == hoy+3 → por_vencer; hoy+4 → sin notificación."""
        ma_limite = self._membresia_con_fin(3)
        self._membresia_con_fin(4)
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        self.assertEqual(
            Notification.objects.get(relacion_tipo='membership', relacion_id=ma_limite.id).tipo,
            'por_vencer'
        )
        # Solo existe la notificación del límite (hoy+4 queda fuera de la ventana)
        self.assertEqual(
            Notification.objects.filter(relacion_tipo='membership').count(), 1
        )

    def test_evento_de_manana_no_genera(self):
        """Edge case: evento con fecha_inicio mañana → sin notificación de evento."""
        manana = date.today() + timedelta(days=1)
        EventoCalendario.objects.create(
            titulo="Clase mañana",
            fecha_inicio=_utc(manana.year, manana.month, manana.day, 10, 0),
            fecha_fin=_utc(manana.year, manana.month, manana.day, 11, 0),
            gimnasio=self.gimnasio,
        )
        NotificationManager.generate_for_gimnasio(self.gimnasio)
        self.assertEqual(Notification.objects.filter(tipo='evento').count(), 0)

    def test_no_genera_para_gimnasio_sin_datos(self):
        """Edge case: gimnasio vacío → generate no crea ninguna notificación."""
        gimnasio_vacio = Gimnasio.objects.create(name="Gym Vacío")
        NotificationManager.generate_for_gimnasio(gimnasio_vacio)
        self.assertEqual(Notification.objects.filter(gimnasio=gimnasio_vacio).count(), 0)


class NotificationViewSetTest(TestCase):
    """Tests del API de notificaciones: permisos, aislamiento, lectura y endpoints."""

    def setUp(self):
        self.gimnasio1 = Gimnasio.objects.create(name="Gym 1")
        self.gimnasio2 = Gimnasio.objects.create(name="Gym 2")
        self.admin1 = Usuario.objects.create_user(
            email="admin1@example.com", name="A", lastname="One",
            password="password123", roles="admin", gimnasio=self.gimnasio1
        )
        self.rec1 = Usuario.objects.create_user(
            email="rec1@example.com", name="R", lastname="One",
            password="password123", roles="recepcion", gimnasio=self.gimnasio1
        )
        self.no_staff = Usuario.objects.create_user(
            email="nope@example.com", name="N", lastname="Ope",
            password="password123", roles="cliente", gimnasio=self.gimnasio1
        )
        self.user2 = Usuario.objects.create_user(
            email="user2@example.com", name="U", lastname="Two",
            password="password123", roles="admin", gimnasio=self.gimnasio2
        )
        self.miembro = UsuarioGym.objects.create(
            name="Ana", lastname="Garcia", gimnasio=self.gimnasio1
        )
        self.membresia = Membresia.objects.create(
            name="Plan 30", price=Decimal('50000'), duration=30, gimnasio=self.gimnasio1
        )
        self.factory = APIRequestFactory()

    def _crear_notificacion(self, gym, tipo='evento', leida=False, relacion_id=None):
        # Cada notificación usa una clave de unicidad distinta. Base alta para
        # no colisionar con ids reales de EventoCalendario/MembresiaAsignada.
        if relacion_id is None:
            self._seq = getattr(self, '_seq', 0) + 1
            relacion_id = 100000 + self._seq
        n = Notification.objects.create(
            gimnasio=gym, tipo=tipo, titulo=f"Notif {tipo}",
            mensaje="Mensaje", fecha=date.today(),
            relacion_tipo='evento', relacion_id=relacion_id,
            link='/dashboard/calendar?evento=999'
        )
        if leida:
            n.is_read = True
            n.read_at = timezone.now()
            n.save(update_fields=['is_read', 'read_at'])
        return n

    def _list(self, user, gym):
        view = NotificationViewSet.as_view({'get': 'list'})
        request = self.factory.get('/')
        request.user = user
        request.gimnasio = gym
        force_authenticate(request, user=user)
        return view(request)

    def test_unauthenticated_list_returns_401(self):
        """Escenario spec: usuario no autenticado → 401."""
        view = NotificationViewSet.as_view({'get': 'list'})
        response = view(self.factory.get('/'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sin_rol_staff_returns_403(self):
        """Escenario spec: usuario que no es admin/recepcion → 403."""
        response = self._list(self.no_staff, self.gimnasio1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_y_recepcion_pueden_listar(self):
        """Escenario spec: admin y recepcion tienen acceso a list/read/count."""
        for user in (self.admin1, self.rec1):
            response = self._list(user, self.gimnasio1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_dispara_generacion_y_retorna_solo_no_leidas(self):
        """Escenario spec: primer list → genera notificaciones y devuelve solo las no leídas."""
        # Dos notificaciones leídas pre-existentes (no deben aparecer)
        self._crear_notificacion(self.gimnasio1, leida=True)
        self._crear_notificacion(self.gimnasio1, leida=True)
        # Datos que disparan generación: membresía por vencer en 2 días + evento hoy
        MembresiaAsignada.objects.create(
            miembro=self.miembro, membresia=self.membresia,
            dateInitial=date.today() - timedelta(days=28)
        )
        EventoCalendario.objects.create(
            titulo="Clase hoy",
            fecha_inicio=_utc(date.today().year, date.today().month, date.today().day, 10, 0),
            fecha_fin=_utc(date.today().year, date.today().month, date.today().day, 11, 0),
            gimnasio=self.gimnasio1,
        )

        response = self._list(self.admin1, self.gimnasio1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tipos = {item['tipo'] for item in response.data}
        self.assertEqual(tipos, {'por_vencer', 'evento'})
        # Las 2 leídas no aparecen y la generación creó 2 nuevas
        self.assertEqual(len(response.data), 2)
        self.assertTrue(all(item['is_read'] is False for item in response.data))

    def test_segundo_list_no_duplica(self):
        """Escenario spec: segunda llamada al list → get_or_create, sin duplicados."""
        MembresiaAsignada.objects.create(
            miembro=self.miembro, membresia=self.membresia,
            dateInitial=date.today() - timedelta(days=28)
        )
        self._list(self.admin1, self.gimnasio1)
        total = Notification.objects.filter(gimnasio=self.gimnasio1).count()
        self._list(self.admin1, self.gimnasio1)
        self.assertEqual(
            Notification.objects.filter(gimnasio=self.gimnasio1).count(), total
        )

    def test_list_aislado_por_gimnasio(self):
        """Escenario spec: usuario del gym B no ve notificaciones del gym A."""
        self._crear_notificacion(self.gimnasio1)
        response = self._list(self.user2, self.gimnasio2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_marcar_leida_setea_read_at_y_oculta(self):
        """Escenario spec: POST {id}/marcar-leida/ → is_read+read_at y desaparece del list."""
        n = self._crear_notificacion(self.gimnasio1)
        view = NotificationViewSet.as_view({'post': 'marcar_leida'})
        request = self.factory.post('/')
        request.user = self.admin1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.admin1)
        response = view(request, pk=n.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)
        # Ya no aparece en el list
        lista = self._list(self.admin1, self.gimnasio1)
        self.assertNotIn(n.id, [item['id'] for item in lista.data])

    def test_marcar_leida_cross_gym_returns_404(self):
        """Aislamiento: usuario del gym B no puede marcar notificaciones del gym A."""
        n = self._crear_notificacion(self.gimnasio1)
        view = NotificationViewSet.as_view({'post': 'marcar_leida'})
        request = self.factory.post('/')
        request.user = self.user2
        request.gimnasio = self.gimnasio2
        force_authenticate(request, user=self.user2)
        response = view(request, pk=n.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_marcar_todas_leidas_marca_todas(self):
        """Escenario spec: POST marcar-todas-leidas/ → todas leídas y list vacío."""
        for _ in range(3):
            self._crear_notificacion(self.gimnasio1)
        view = NotificationViewSet.as_view({'post': 'marcar_todas_leidas'})
        request = self.factory.post('/')
        request.user = self.admin1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.admin1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['marked'], 3)
        self.assertFalse(
            Notification.objects.filter(gimnasio=self.gimnasio1, is_read=False).exists()
        )
        lista = self._list(self.admin1, self.gimnasio1)
        self.assertEqual(lista.data, [])

    def test_no_leidas_retorna_conteo(self):
        """Escenario spec: GET no-leidas/ → {"count": N} con solo no leídas."""
        self._crear_notificacion(self.gimnasio1)
        self._crear_notificacion(self.gimnasio1)
        self._crear_notificacion(self.gimnasio1, leida=True)
        view = NotificationViewSet.as_view({'get': 'no_leidas'})
        request = self.factory.get('/')
        request.user = self.admin1
        request.gimnasio = self.gimnasio1
        force_authenticate(request, user=self.admin1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'count': 2})

    def test_endpoints_legacy_removed_returns_404(self):
        """Escenario spec: los endpoints legacy eliminados responden 404."""
        self.assertEqual(
            self.client.get('/gym/api/v1/membership-notifications/').status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.post('/gym/api/v1/membership-notifications/read/', {}).status_code,
            status.HTTP_404_NOT_FOUND,
        )
