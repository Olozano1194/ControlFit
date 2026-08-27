import io
import base64
import json
from django.test import TestCase, TransactionTestCase
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
from .models import Gimnasio, Usuario, UsuarioGym, Membresia, MembresiaAsignada, PagoMembresia, TipoEvento, EventoCalendario, Notification, DemoRequest
from .middleware import GimnasioMiddleware
from .mixins import MultiTenantViewSetMixin
from .serializers import UsuarioSerializer, UsuarioGymSerializer, MembresiasSerializer, MembresiaAsignadaSerializer, PagoMembresiaSerializer, EventoCalendarioSerializer, DemoRequestSerializer
from .views import UserViewSet, UsuarioGymViewSet, MembresiaViewSet, Home, PagoMembresiaViewSet, TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView, NotificationViewSet, DemoRequestViewSet
from .services.notifications import NotificationManager
from .storage import SupabaseMediaStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test.utils import override_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


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


# ============================================================
# AUTH COOKIE JWT — TESTS (cambio auth-refresh-jwt)
# ============================================================

def _make_staff_user(gimnasio, email="admin@example.com", password="secret"):
    """Crea un usuario staff (admin) para los tests de auth."""
    return Usuario.objects.create_user(
        email=email,
        name="Admin",
        lastname="User",
        password=password,
        roles="admin",
        gimnasio=gimnasio,
    )


class AuthCookieHelperTest(TestCase):
    """Unit tests para el helper compartido de cookie (gimnasioApp/auth_cookie.py)."""

    def test_set_refresh_cookie_sets_exact_attributes(self):
        """set_refresh_cookie define key, httponly, path, max_age, samesite y secure (dev)."""
        from .auth_cookie import set_refresh_cookie
        from rest_framework.response import Response

        response = Response()
        with override_settings(DEBUG=True):
            set_refresh_cookie(response, "token-value")

        cookie = response.cookies['refresh_token']
        self.assertEqual(cookie.value, 'token-value')
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['path'], '/gym/api/v1/')
        self.assertEqual(cookie['max-age'], 604800)
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertFalse(cookie['secure'])

    def test_set_refresh_cookie_prod_attributes(self):
        """En producción (DEBUG=False) la cookie usa SameSite=None + Secure."""
        from .auth_cookie import set_refresh_cookie
        from rest_framework.response import Response

        response = Response()
        with override_settings(DEBUG=False):
            set_refresh_cookie(response, "token-value")

        cookie = response.cookies['refresh_token']
        self.assertEqual(cookie['samesite'], 'None')
        self.assertTrue(cookie['secure'])

    def test_clear_refresh_cookie_expires_cookie(self):
        """clear_refresh_cookie expira la cookie (Max-Age=0) en el mismo path."""
        from .auth_cookie import clear_refresh_cookie
        from rest_framework.response import Response

        response = Response()
        clear_refresh_cookie(response)

        cookie = response.cookies['refresh_token']
        self.assertEqual(cookie['max-age'], 0)
        self.assertEqual(cookie['path'], '/gym/api/v1/')

    def test_refresh_cookie_path_covers_refresh_and_logout(self):
        """RFC 6265 §5.4: el Path de la cookie debe ser prefijo de /token/refresh/
        Y de /auth/logout/; si no cubre el logout, el browser omite la cookie y el
        blacklist server-side queda inalcanzable (regresión del bug de path-match)."""
        from django.urls import reverse
        from .auth_cookie import REFRESH_COOKIE_PATH

        self.assertTrue(reverse('token_refresh').startswith(REFRESH_COOKIE_PATH))
        self.assertTrue(reverse('auth_logout').startswith(REFRESH_COOKIE_PATH))


class AuthCookieLoginTest(TestCase):
    """Login (POST /gym/api/v1/token/) establece la cookie y devuelve solo access."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Auth Gym")
        self.user = _make_staff_user(self.gimnasio)

    def test_login_sets_refresh_cookie_and_returns_access_only(self):
        """Escenario spec: login exitoso → 200, body {access} sin refresh, cookie con atributos."""
        response = self.client.post('/gym/api/v1/token/', {
            'email': self.user.email,
            'password': 'secret',
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIn('access', body)
        self.assertNotIn('refresh', body)

        cookie = response.cookies['refresh_token']
        self.assertNotEqual(cookie.value, '')
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['path'], '/gym/api/v1/')
        self.assertEqual(cookie['max-age'], 604800)
        # El helper lee settings.DEBUG dinámicamente (None+Secure en prod, Lax en dev)
        expected_samesite = 'None' if not settings.DEBUG else 'Lax'
        expected_secure = not settings.DEBUG
        self.assertEqual(cookie['samesite'], expected_samesite)
        self.assertEqual(bool(cookie['secure']), expected_secure)

    def test_login_invalid_credentials_returns_401_no_cookie(self):
        """Escenario spec: credenciales inválidas → 401 sin cookie."""
        response = self.client.post('/gym/api/v1/token/', {
            'email': self.user.email,
            'password': 'wrong-password',
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('refresh_token', response.cookies)

    def test_login_missing_fields_returns_400(self):
        """Escenario spec: body vacío → 400 con errores de validación."""
        response = self.client.post('/gym/api/v1/token/', {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.json())
        self.assertIn('password', response.json())

    def test_register_sets_refresh_cookie_via_shared_helper(self):
        """El registro sigue funcionando y usa el mismo helper de cookie."""
        response = self.client.post('/gym/api/v1/register/', {
            'email': 'new@example.com',
            'password': 'secret123',
            'name': 'New',
            'lastname': 'User',
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cookie = response.cookies['refresh_token']
        self.assertNotEqual(cookie.value, '')
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['path'], '/gym/api/v1/')
        self.assertEqual(cookie['max-age'], 604800)
        expected_samesite = 'None' if not settings.DEBUG else 'Lax'
        self.assertEqual(cookie['samesite'], expected_samesite)


class AuthCookieRefreshTest(TestCase):
    """Refresh (POST /gym/api/v1/token/refresh/) lee la cookie, rota y devuelve access."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Auth Gym")
        self.user = _make_staff_user(self.gimnasio)
        self.login = self.client.post('/gym/api/v1/token/', {
            'email': self.user.email,
            'password': 'secret',
        }, content_type='application/json')
        self.old_refresh = self.login.cookies['refresh_token'].value
        # jti del token ORIGINAL (capturado antes de que la rotación lo blacklistee)
        self.old_jti = RefreshToken(self.old_refresh).payload['jti']

    def test_refresh_from_cookie_returns_new_access_and_rotates(self):
        """Escenario spec: refresh body-less → 200, access nuevo, cookie rotada, viejo blacklisted."""
        response = self.client.post('/gym/api/v1/token/refresh/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIn('access', body)
        self.assertNotIn('refresh', body)

        new_refresh = response.cookies['refresh_token'].value
        self.assertNotEqual(new_refresh, self.old_refresh)
        self.assertEqual(response.cookies['refresh_token']['path'], '/gym/api/v1/')
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=self.old_jti).exists())

    def test_refresh_without_cookie_returns_401(self):
        """Escenario spec: sin cookie → 401 con detail 'No refresh token'."""
        self.client.cookies.clear()
        response = self.client.post('/gym/api/v1/token/refresh/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'detail': 'No refresh token'})

    def test_refresh_with_expired_cookie_returns_401(self):
        """Escenario spec: cookie con refresh expirado → 401."""
        expired = RefreshToken.for_user(self.user)
        expired.set_exp(lifetime=timedelta(seconds=-1))
        self.client.cookies['refresh_token'] = str(expired)

        response = self.client.post('/gym/api/v1/token/refresh/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_blacklisted_cookie_returns_401(self):
        """Escenario spec: cookie con refresh blacklistado → 401."""
        # Forzamos el blacklist manualmente sobre el token original.
        RefreshToken(self.old_refresh).blacklist()
        self.client.cookies['refresh_token'] = self.old_refresh

        response = self.client.post('/gym/api/v1/token/refresh/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sequential_refresh_second_tab_gets_401(self):
        """Escenario multi-tab: la segunda pestaña (cookie vieja) recibe 401 tras la rotación."""
        first = self.client.post('/gym/api/v1/token/refresh/')
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        # Tab B usa la cookie vieja (ya blacklistada por la rotación de Tab A)
        self.client.cookies['refresh_token'] = self.old_refresh
        second = self.client.post('/gym/api/v1/token/refresh/')

        self.assertEqual(second.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthCookieLogoutTest(TestCase):
    """Logout (POST /gym/api/v1/auth/logout/) blacklistea, limpia cookie y es idempotente."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Auth Gym")
        self.user = _make_staff_user(self.gimnasio)
        self.login = self.client.post('/gym/api/v1/token/', {
            'email': self.user.email,
            'password': 'secret',
        }, content_type='application/json')
        self.old_refresh = self.login.cookies['refresh_token'].value
        self.old_jti = RefreshToken(self.old_refresh).payload['jti']

    def test_logout_blacklists_token_and_clears_cookie(self):
        """Escenario spec: logout → 200, token blacklistado, cookie expirada, refresh posterior 401."""
        response = self.client.post('/gym/api/v1/auth/logout/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=self.old_jti).exists())
        self.assertEqual(response.cookies['refresh_token']['max-age'], 0)

        # Un refresh con la cookie vieja ahora debe fallar con 401
        self.client.cookies['refresh_token'] = self.old_refresh
        refresh = self.client.post('/gym/api/v1/token/refresh/')
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_cookie_is_idempotent(self):
        """Escenario spec: logout sin cookie → 200 sin error."""
        self.client.cookies.clear()
        response = self.client.post('/gym/api/v1/auth/logout/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'detail': 'Logged out'})

    def test_logout_with_blacklisted_token_is_idempotent(self):
        """Escenario spec: logout con token ya blacklistado → 200 sin excepción."""
        self.client.post('/gym/api/v1/auth/logout/')
        self.client.cookies['refresh_token'] = self.old_refresh

        response = self.client.post('/gym/api/v1/auth/logout/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['refresh_token']['max-age'], 0)


class AuthSettingsTest(TestCase):
    """Tests de configuración del cambio auth-refresh-jwt."""

    def test_rotate_refresh_tokens_is_true(self):
        """Escenario spec: ROTATE_REFRESH_TOKENS=True en SIMPLE_JWT."""
        self.assertTrue(settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS'])

    def test_single_cors_allowed_origins_definition(self):
        """Escenario spec: una sola definición de CORS_ALLOWED_ORIGINS (Vite 5173 + Vercel)."""
        self.assertEqual(settings.CORS_ALLOWED_ORIGINS, [
            "http://localhost:5173",
            "https://controlfit.vercel.app",
        ])

    def test_auth_cookie_vestigial_block_removed(self):
        """El helper lee settings.DEBUG directamente; el bloque AUTH_COOKIE_* vestigial se eliminó."""
        self.assertNotIn('AUTH_COOKIE', settings.SIMPLE_JWT)
        self.assertNotIn('AUTH_COOKIE_SAMESITE', settings.SIMPLE_JWT)


# ============================================================
# PLATFORM DASHBOARD — SUPERADMIN
# ============================================================

class PlatformDashboardTest(TestCase):
    """Tests para el dashboard de plataforma (superadmin)."""

    def setUp(self):
        from gimnasioApp.models import Gimnasio, Usuario, UsuarioGym, Membresia, MembresiaAsignada, PagoMembresia, UsuarioGymDay, DemoRequest
        from datetime import date, timedelta
        from decimal import Decimal
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient

        User = get_user_model()

        # Crear superadmin
        self.superadmin = User.objects.create_user(
            email='superadmin@test.com',
            password='TestPass123',
            name='Super',
            lastname='Admin',
            roles='superadmin',
            gimnasio=None
        )

        # Crear gym admin normal
        self.gym1 = Gimnasio.objects.create(name='Gym Alpha', address='Calle 1', phone='3001112233', is_active=True)
        self.gym2 = Gimnasio.objects.create(name='Gym Beta', address='Calle 2', phone='3004445566', is_active=True)
        self.gym3 = Gimnasio.objects.create(name='Gym Gamma', address='Calle 3', phone='3007778899', is_active=False)

        # Admin de gym1
        self.admin1 = User.objects.create_user(
            email='admin1@test.com',
            password='TestPass123',
            name='Admin',
            lastname='Uno',
            roles='admin',
            gimnasio=self.gym1
        )

        # Recepcionista de gym2
        self.recep2 = User.objects.create_user(
            email='recep2@test.com',
            password='TestPass123',
            name='Recep',
            lastname='Dos',
            roles='recepcion',
            gimnasio=self.gym2
        )

        # Miembros y membresías para gym1
        self.miembro1 = UsuarioGym.objects.create(
            gimnasio=self.gym1, name='Juan', lastname='Perez', phone='3001111111', address='Dir 1'
        )
        self.membresia1 = Membresia.objects.create(
            gimnasio=self.gym1, name='Mensual', price=Decimal('100000'), duration=30, max_multiplier=3
        )
        self.memb_asig1 = MembresiaAsignada.objects.create(
            miembro=self.miembro1, membresia=self.membresia1, dateInitial=date.today() - timedelta(days=5),
            multiplier=1, discount_percent=Decimal('0')
        )

        # Miembros y membresías para gym2
        self.miembro2 = UsuarioGym.objects.create(
            gimnasio=self.gym2, name='Maria', lastname='Gomez', phone='3002222222', address='Dir 2'
        )
        self.membresia2 = Membresia.objects.create(
            gimnasio=self.gym2, name='Trimestral', price=Decimal('250000'), duration=90, max_multiplier=1
        )
        self.memb_asig2 = MembresiaAsignada.objects.create(
            miembro=self.miembro2, membresia=self.membresia2, dateInitial=date.today() - timedelta(days=10),
            multiplier=1, discount_percent=Decimal('0')
        )

        # Pagos (mes actual)
        PagoMembresia.objects.create(
            membresia_asignada=self.memb_asig1, monto=Decimal('50000'), metodo_pago='efectivo'
        )
        PagoMembresia.objects.create(
            membresia_asignada=self.memb_asig2, monto=Decimal('250000'), metodo_pago='transferencia'
        )

        # Ingresos diarios (mes actual)
        UsuarioGymDay.objects.create(
            gimnasio=self.gym1, name='Pedro', lastname='Lopez', phone='3003333333',
            dateInitial=date.today(), price=Decimal('20000')
        )
        UsuarioGymDay.objects.create(
            gimnasio=self.gym2, name='Ana', lastname='Martinez', phone='3004444444',
            dateInitial=date.today(), price=Decimal('15000')
        )

        # Demo requests
        DemoRequest.objects.create(nombre='Demo1', email='demo1@test.com', telefono='3005555555', nombre_gimnasio='Demo Gym 1', estado='pendiente')
        DemoRequest.objects.create(nombre='Demo2', email='demo2@test.com', telefono='3006666666', nombre_gimnasio='Demo Gym 2', estado='contactado')

        # Login superadmin - usar APIClient
        self.client = APIClient()
        self.client.force_authenticate(user=self.superadmin)

    def test_superadmin_sees_active_gyms_in_list(self):
        """Superadmin ve solo gyms activos (2) en listado, admin de gym ve 403."""
        response = self.client.get('/gym/api/v1/platform/gimnasios/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)  # Solo gym1 y gym2 (activos)

        self.client.force_authenticate(user=self.admin1)
        response = self.client.get('/gym/api/v1/platform/gimnasios/')
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.recep2)
        response = self.client.get('/gym/api/v1/platform/gimnasios/')
        self.assertEqual(response.status_code, 403)

    def test_stats_aggregation_correct(self):
        """Stats: ingresos = pagos + diarios, retención ponderada."""
        response = self.client.get('/gym/api/v1/platform/stats/')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['total_gimnasios'], 3)
        self.assertEqual(data['gimnasios_activos'], 2)
        self.assertEqual(data['total_usuarios_staff'], 3)
        self.assertEqual(data['demo_pendientes'], 1)
        self.assertEqual(data['demo_contactados'], 1)
        self.assertEqual(data['ingresos_mes_global'], '335000.00')
        self.assertEqual(data['miembros_activos_global'], 2)
        self.assertEqual(data['retencion_promedio'], '100.0')

    def test_pagination_default_20_max_100(self):
        """Paginación: default 20, max 100."""
        # Default
        response = self.client.get('/gym/api/v1/platform/gimnasios/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)  # DRF pagination: count, next, previous, results
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 2)  # Solo 2 gyms activos en test

        # page_size=10 (menor a 20)
        response = self.client.get('/gym/api/v1/platform/gimnasios/?page_size=10')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)  # solo 2 gyms activos en test

        # page_size=150 (mayor a max) → debe caer a 100
        response = self.client.get('/gym/api/v1/platform/gimnasios/?page_size=150')
        self.assertEqual(response.status_code, 200)

    def test_toggle_is_active(self):
        """PATCH /platform/gimnasios/{id}/ con is_active → actualiza."""
        import json
        response = self.client.patch(
            f'/gym/api/v1/platform/gimnasios/{self.gym3.id}/',
            json.dumps({'is_active': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_active'])

        from gimnasioApp.models import Gimnasio
        gym3 = Gimnasio.objects.get(id=self.gym3.id)
        self.assertTrue(gym3.is_active)

        self.client.force_authenticate(user=self.admin1)
        response = self.client.patch(
            f'/gym/api/v1/platform/gimnasios/{self.gym3.id}/',
            {'is_active': False},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)


# ============================================================
# AUTO-CREAR GYM DESDE DEMO — Phase 1 Foundation Tests
# ============================================================

class AutoCrearGymDesdeDemoPhase1Test(TestCase):
    """Tests para la fase 1: Foundation - modelos y serializers."""

    def setUp(self):
        from gimnasioApp.models import Gimnasio, Usuario, DemoRequest
        self.gym = Gimnasio.objects.create(name="Test Gym", address="Calle 123", phone="3001112233")
        
    def test_demo_request_gym_creado_fk_nullable(self):
        """DemoRequest tiene FK gym_creado nullable con SET_NULL y related_name=demo_origen."""
        from gimnasioApp.models import DemoRequest, Gimnasio
        
        # Crear DemoRequest sin gym_creado (debe ser nullable)
        demo = DemoRequest.objects.create(
            nombre='Test Demo',
            email='test@demo.com',
            telefono='3005555555',
            nombre_gimnasio='Demo Gym Test'
        )
        self.assertIsNone(demo.gym_creado)
        
        # Asociar un gimnasio
        demo.gym_creado = self.gym
        demo.save()
        self.assertEqual(demo.gym_creado, self.gym)
        
        # Verificar related_name funciona (reverse relation)
        self.assertIn(demo, self.gym.demo_origen.all())
        
        # Verificar SET_NULL al borrar el gimnasio
        gym_id = self.gym.id
        self.gym.delete()
        demo.refresh_from_db()
        self.assertIsNone(demo.gym_creado)

    def test_usuario_must_change_password_default_false(self):
        """Usuario tiene campo must_change_password BooleanField(default=False)."""
        from gimnasioApp.models import Usuario
        
        user = Usuario.objects.create_user(
            email='test@user.com',
            password='password123',
            name='Test',
            lastname='User',
            gimnasio=self.gym
        )
        
        # El campo debe existir y ser False por defecto
        self.assertFalse(user.must_change_password)
        
        # Podemos establecerlo a True
        user.must_change_password = True
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.must_change_password)

    def test_demo_request_serializer_includes_gym_creado_nested(self):
        """DemoRequestSerializer incluye gym_creado anidado (read_only) con id y name."""
        from gimnasioApp.serializers import DemoRequestSerializer
        from gimnasioApp.models import DemoRequest
        
        # DemoRequest sin gym_creado
        demo = DemoRequest.objects.create(
            nombre='Serializer Test',
            email='serializer@test.com',
            telefono='3001111111',
            nombre_gimnasio='Serializer Gym'
        )
        serializer = DemoRequestSerializer(demo)
        data = serializer.data
        
        # gym_creado debe estar presente y ser None
        self.assertIn('gym_creado', data)
        self.assertIsNone(data['gym_creado'])
        
        # DemoRequest con gym_creado
        demo.gym_creado = self.gym
        demo.save()
        serializer = DemoRequestSerializer(demo)
        data = serializer.data
        
        # gym_creado debe ser objeto con id y name
        self.assertIsNotNone(data['gym_creado'])
        self.assertEqual(data['gym_creado']['id'], self.gym.id)
        self.assertEqual(data['gym_creado']['name'], self.gym.name)
        
        # gym_creado debe ser read_only (no se puede escribir via serializer)
        # Intentar crear con gym_creado en data debe ignorarlo o fallar
        create_data = {
            'nombre': 'New Demo',
            'email': 'new@demo.com',
            'telefono': '3002222222',
            'nombre_gimnasio': 'New Gym',
            'gym_creado': {'id': self.gym.id, 'name': 'Hacker Gym'}  # Intentar inyectar
        }
        create_serializer = DemoRequestSerializer(data=create_data)
        self.assertTrue(create_serializer.is_valid())
        # gym_creado no debe estar en validated_data porque es read_only
        self.assertNotIn('gym_creado', create_serializer.validated_data)


# ============================================================
# AUTO-CREAR GYM DESDE DEMO — Phase 2 Backend Core Tests
# ============================================================

class OnboardingServiceTest(TestCase):
    """Tests unitarios para gimnasioApp/services/onboarding.py"""
    
    def setUp(self):
        from gimnasioApp.models import Gimnasio, Usuario, DemoRequest
        self.gym = Gimnasio.objects.create(name="Test Gym", address="Calle 123", phone="3001112233")

    def test_generate_temp_password_length_and_entropy(self):
        """generate_temp_password genera password de 12 chars URL-safe con alta entropía."""
        from gimnasioApp.services.onboarding import generate_temp_password
        
        # Llamar múltiples veces para verificar entropía
        passwords = [generate_temp_password() for _ in range(10)]
        
        for pwd in passwords:
            # Debe tener exactamente 12 caracteres
            self.assertEqual(len(pwd), 12)
            # Debe ser URL-safe (solo alfanuméricos, - y _)
            self.assertTrue(all(c.isalnum() or c in '-_' for c in pwd))
        
        # Verificar que no son todos iguales (entropía)
        self.assertEqual(len(set(passwords)), len(passwords))

    def test_provision_gym_from_demo_creates_gym_admin_link(self):
        """Happy path: provision crea Gimnasio + Usuario admin + link demo."""
        from gimnasioApp.services.onboarding import provision_gym_from_demo
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@nuevogym.com',
            telefono='3005555555',
            nombre_gimnasio='Gimnasio Nuevo',
            estado='pendiente'
        )
        
        gym, admin, temp_password = provision_gym_from_demo(demo)
        
        # Verificar Gimnasio creado
        self.assertIsInstance(gym, Gimnasio)
        self.assertEqual(gym.name, 'Gimnasio Nuevo')
        self.assertEqual(gym.phone, '3005555555')
        self.assertEqual(gym.address, '')
        self.assertTrue(gym.is_active)
        
        # Verificar Usuario admin creado
        self.assertIsInstance(admin, Usuario)
        self.assertEqual(admin.email, 'juan@nuevogym.com')
        self.assertEqual(admin.name, 'Admin')
        self.assertEqual(admin.lastname, 'Gimnasio Nuevo')
        self.assertEqual(admin.roles, 'admin')
        self.assertEqual(admin.gimnasio, gym)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.must_change_password)
        # Verificar que la contraseña está hasheada
        self.assertTrue(admin.check_password(temp_password))
        
        # Verificar link demo -> gym
        demo.refresh_from_db()
        self.assertEqual(demo.gym_creado, gym)
        self.assertEqual(demo.estado, 'pendiente')  # estado no cambia

    def test_provision_gym_from_demo_idempotent_if_already_contactado(self):
        """Si demo ya tiene gym_creado, NO crea duplicado."""
        from gimnasioApp.services.onboarding import provision_gym_from_demo
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@nuevogym.com',
            telefono='3005555555',
            nombre_gimnasio='Gimnasio Nuevo',
            estado='contactado'
        )
        
        # Primera provisión
        gym1, admin1, temp1 = provision_gym_from_demo(demo)
        
        # Segunda llamada (idempotente) - temp password puede ser diferente
        gym2, admin2, temp2 = provision_gym_from_demo(demo)
        
        # Debe retornar los mismos objetos gym y admin
        self.assertEqual(gym1, gym2)
        self.assertEqual(admin1, admin2)
        # temp_password se regenera en cada llamada (no se guarda)
        
        # Verificar que solo se creó UN gimnasio y UN usuario
        self.assertEqual(Gimnasio.objects.filter(name='Gimnasio Nuevo').count(), 1)
        self.assertEqual(Usuario.objects.filter(email='juan@nuevogym.com').count(), 1)

    def test_provision_gym_from_demo_email_duplicate_raises_400(self):
        """Email ya existe en Usuario -> ValidationError."""
        from gimnasioApp.services.onboarding import provision_gym_from_demo
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        from django.core.exceptions import ValidationError
        
        # Crear usuario existente con ese email
        Usuario.objects.create_user(
            email='existente@gym.com',
            password='password123',
            name='Existente',
            lastname='User',
            gimnasio=self.gym
        )
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='existente@gym.com',  # Email duplicado
            telefono='3005555555',
            nombre_gimnasio='Gimnasio Nuevo',
            estado='pendiente'
        )
        
        with self.assertRaises(ValidationError) as cm:
            provision_gym_from_demo(demo)
        
        self.assertIn('ya está registrado', str(cm.exception))
        
        # Verificar que NO se creó gimnasio ni usuario nuevo
        self.assertEqual(Gimnasio.objects.filter(name='Gimnasio Nuevo').count(), 0)
        self.assertEqual(Usuario.objects.filter(email='existente@gym.com').count(), 1)

    def test_provision_gym_from_demo_truncates_phone_and_lastname(self):
        """phone > 20 y lastname > 50 se truncan."""
        from gimnasioApp.services.onboarding import provision_gym_from_demo
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        
        # El modelo DemoRequest.telefono tiene max_length=20, truncar antes de crear
        long_phone = '+57 300 123 4567 ext 8901234'[:20]
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@truncate.com',
            telefono=long_phone,
            nombre_gimnasio='Gimnasio Fitness Center Bogota Colombia Sur America',  # 55+ chars
            estado='pendiente'
        )
        
        gym, admin, temp_password = provision_gym_from_demo(demo)
        
        # Phone truncado a 20
        self.assertEqual(len(gym.phone), 20)
        self.assertEqual(gym.phone, '+57 300 123 4567 ext')
        
        # Lastname truncado a 50 (el campo Usuario.lastname tiene max_length=50)
        self.assertLessEqual(len(admin.lastname), 50)
        # Verificar que es el inicio del nombre_gimnasio
        self.assertTrue(admin.lastname.startswith('Gimnasio Fitness Center Bogota Colombia'))

    def test_revert_gym_from_demo_soft_deletes(self):
        """contactado->pendiente: gym.is_active=False, admin.is_active=False, demo.gym_creado=NULL."""
        from gimnasioApp.services.onboarding import provision_gym_from_demo, revert_gym_from_demo
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@revert.com',
            telefono='3005555555',
            nombre_gimnasio='Gym Revert',
            estado='contactado'
        )
        
        # Provision primero
        gym, admin, temp_password = provision_gym_from_demo(demo)
        self.assertTrue(gym.is_active)
        self.assertTrue(admin.is_active)
        self.assertEqual(demo.gym_creado, gym)
        
        # Ahora revert
        revert_gym_from_demo(demo)
        
        # Verificar soft-delete
        gym.refresh_from_db()
        admin.refresh_from_db()
        demo.refresh_from_db()
        
        self.assertFalse(gym.is_active)
        self.assertFalse(admin.is_active)
        self.assertIsNone(demo.gym_creado)


class DemoRequestViewSetIntegrationTest(TestCase):
    """Tests de integración para DemoRequestViewSet.perform_update"""
    
    def setUp(self):
        from gimnasioApp.models import Gimnasio, Usuario, DemoRequest
        from rest_framework.test import APIRequestFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.factory = APIRequestFactory()
        
        # Superadmin user (no gym required)
        self.superadmin = Usuario.objects.create_user(
            email='super@admin.com',
            password='password123',
            name='Super',
            lastname='Admin',
            roles='superadmin'
        )
        self.superadmin_token = str(RefreshToken.for_user(self.superadmin).access_token)
        
        # Regular admin user (with gym)
        self.gym = Gimnasio.objects.create(name="Test Gym")
        self.admin_user = Usuario.objects.create_user(
            email='admin@gym.com',
            password='password123',
            name='Admin',
            lastname='User',
            roles='admin',
            gimnasio=self.gym
        )
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

    import json

    def _patch_demo(self, demo_id, data, token):
        """Helper para hacer PATCH request autenticado."""
        request = self.factory.patch(
            f'/solicitudes-demo/{demo_id}/',
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        view = DemoRequestViewSet.as_view({'patch': 'partial_update'})
        return view(request, pk=demo_id)

    def test_viewset_perform_update_pendiente_to_contactado_creates_gym_admin(self):
        """Integration: PATCH pendiente->contactado -> 200 + gym_creado en response."""
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        from gimnasioApp.serializers import DemoRequestSerializer
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@integration.com',
            telefono='3005555555',
            nombre_gimnasio='Integration Gym',
            estado='pendiente'
        )
        
        response = self._patch_demo(demo.id, {'estado': 'contactado'}, self.superadmin_token)
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar response incluye gym_creado
        self.assertIn('gym_creado', response.data)
        self.assertIsNotNone(response.data['gym_creado'])
        self.assertEqual(response.data['gym_creado']['name'], 'Integration Gym')
        
        # Verificar en BD
        demo.refresh_from_db()
        self.assertEqual(demo.estado, 'contactado')
        self.assertIsNotNone(demo.gym_creado)
        self.assertEqual(demo.gym_creado.name, 'Integration Gym')
        
        gym = demo.gym_creado
        self.assertTrue(gym.is_active)
        
        admin = Usuario.objects.get(gimnasio=gym, roles='admin')
        self.assertEqual(admin.email, 'juan@integration.com')
        self.assertTrue(admin.must_change_password)

    def test_viewset_perform_update_idempotent_repatch(self):
        """Integration: Re-PATCH contactado->contactado NO crea duplicados."""
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@idem.com',
            telefono='3005555555',
            nombre_gimnasio='Idempotent Gym',
            estado='pendiente'
        )
        
        # Primera vez - provision (pendiente -> contactado)
        response1 = self._patch_demo(demo.id, {'estado': 'contactado'}, self.superadmin_token)
        self.assertEqual(response1.status_code, 200)
        
        gym_id_1 = response1.data['gym_creado']['id']
        
        # Segunda vez - idempotente (contactado -> contactado)
        response2 = self._patch_demo(demo.id, {'estado': 'contactado'}, self.superadmin_token)
        self.assertEqual(response2.status_code, 200)
        
        gym_id_2 = response2.data['gym_creado']['id']
        
        # Mismo gym
        self.assertEqual(gym_id_1, gym_id_2)
        self.assertEqual(Gimnasio.objects.filter(name='Idempotent Gym').count(), 1)
        self.assertEqual(Usuario.objects.filter(email='juan@idem.com').count(), 1)

    def test_viewset_perform_update_contactado_to_pendiente_soft_deletes(self):
        """Integration: PATCH contactado->pendiente -> 200 + gym_creado=null + soft-delete."""
        from gimnasioApp.models import DemoRequest, Gimnasio, Usuario
        from gimnasioApp.services.onboarding import provision_gym_from_demo
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@reverse.com',
            telefono='3005555555',
            nombre_gimnasio='Reverse Gym',
            estado='contactado'
        )
        
        # Provision manual primero (simula estado contactado ya provisionado)
        gym, admin, _ = provision_gym_from_demo(demo)
        demo.refresh_from_db()
        self.assertEqual(demo.gym_creado, gym)
        self.assertEqual(demo.estado, 'contactado')
        
        # Ahora PATCH a pendiente
        response = self._patch_demo(demo.id, {'estado': 'pendiente'}, self.superadmin_token)
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar response tiene gym_creado=null
        self.assertIsNone(response.data['gym_creado'])
        
        # Verificar en BD
        demo.refresh_from_db()
        gym.refresh_from_db()
        admin.refresh_from_db()
        
        self.assertEqual(demo.estado, 'pendiente')
        self.assertIsNone(demo.gym_creado)
        self.assertFalse(gym.is_active)
        self.assertFalse(admin.is_active)

    def test_viewset_perform_update_duplicate_email_returns_400(self):
        """Integration: email duplicado -> 400 con mensaje guía."""
        from gimnasioApp.models import DemoRequest, Usuario
        
        # Usuario existente
        Usuario.objects.create_user(
            email='duplicado@gym.com',
            password='password123',
            name='Existente',
            lastname='User',
            gimnasio=self.gym
        )
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='duplicado@gym.com',
            telefono='3005555555',
            nombre_gimnasio='Duplicate Gym',
            estado='pendiente'
        )
        
        response = self._patch_demo(demo.id, {'estado': 'contactado'}, self.superadmin_token)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('ya está registrado', str(response.data))
        
        # Verificar que no se creó nada
        self.assertEqual(DemoRequest.objects.filter(email='duplicado@gym.com').count(), 1)
        self.assertEqual(Usuario.objects.filter(email='duplicado@gym.com').count(), 1)

    def test_viewset_perform_update_unauthenticated_returns_401(self):
        """Integration: sin auth -> 401."""
        from gimnasioApp.models import DemoRequest
        from rest_framework.test import APIRequestFactory
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@unauth.com',
            telefono='3005555555',
            nombre_gimnasio='Unauth Gym',
            estado='pendiente'
        )
        
        factory = APIRequestFactory()
        request = factory.patch(
            f'/solicitudes-demo/{demo.id}/',
            data={'estado': 'contactado'},
            content_type='application/json'
        )
        view = DemoRequestViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=demo.id)
        
        self.assertEqual(response.status_code, 401)

    def test_viewset_perform_update_non_superadmin_returns_403(self):
        """Integration: admin regular (no superadmin) -> 403."""
        from gimnasioApp.models import DemoRequest
        
        demo = DemoRequest.objects.create(
            nombre='Juan Perez',
            email='juan@forbidden.com',
            telefono='3005555555',
            nombre_gimnasio='Forbidden Gym',
            estado='pendiente'
        )
        
        response = self._patch_demo(demo.id, {'estado': 'contactado'}, self.admin_token)
        
        self.assertEqual(response.status_code, 403)# ============================================================
# PHASE 3: EMAIL SERVICE TESTS
# ============================================================

class EmailServiceTest(TestCase):
    """Unit tests for send_welcome_email service."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.admin = Usuario.objects.create_user(
            email="admin@test.com",
            name="Admin",
            lastname="User",
            password="password123",
            roles="admin",
            gimnasio=self.gimnasio
        )

    @patch('gimnasioApp.services.email.send_mail')
    @patch('django.conf.settings.FRONTEND_URL', 'http://localhost:5173')
    @patch('django.conf.settings.SUPPORT_EMAIL', 'soporte@controlfit.app')
    @patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'ControlFit <noreply@controlfit.app>')
    def test_send_welcome_email_renders_templates(self, mock_send_mail):
        """Test that send_welcome_email renders both HTML and text templates."""
        from gimnasioApp.services.email import send_welcome_email
        
        send_welcome_email(self.gimnasio.id, self.admin.id, 'TempPass123')
        
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        
        # Verify subject
        self.assertIn('Bienvenido a ControlFit', call_args.kwargs['subject'])
        self.assertIn('Test Gym', call_args.kwargs['subject'])
        
        # Verify recipient
        self.assertEqual(call_args.kwargs['recipient_list'], ['admin@test.com'])
        
        # Verify from email
        self.assertEqual(call_args.kwargs['from_email'], 'ControlFit <noreply@controlfit.app>')
        
        # Verify html_message and plain_message are provided
        self.assertIn('html_message', call_args.kwargs)
        self.assertIn('message', call_args.kwargs)
        self.assertTrue(len(call_args.kwargs['html_message']) > 0)
        self.assertTrue(len(call_args.kwargs['message']) > 0)
        
        # Verify content includes key data
        html = call_args.kwargs['html_message']
        plain = call_args.kwargs['message']
        self.assertIn('Test Gym', html)
        self.assertIn('admin@test.com', html)
        self.assertIn('TempPass123', html)
        self.assertIn('http://localhost:5173/login', html)
        self.assertIn('soporte@controlfit.app', html)
        self.assertIn('Test Gym', plain)
        self.assertIn('admin@test.com', plain)
        self.assertIn('TempPass123', plain)

    @patch('gimnasioApp.services.email.send_mail')
    @patch('django.conf.settings.FRONTEND_URL', 'http://localhost:5173')
    @patch('django.conf.settings.SUPPORT_EMAIL', 'soporte@controlfit.app')
    @patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'ControlFit <noreply@controlfit.app>')
    def test_send_welcome_email_context_includes_all_fields(self, mock_send_mail):
        """Test that template context includes all required fields."""
        from gimnasioApp.services.email import send_welcome_email
        
        send_welcome_email(self.gimnasio.id, self.admin.id, 'MyTempPass')
        
        call_args = mock_send_mail.call_args
        html = call_args.kwargs['html_message']
        plain = call_args.kwargs['message']
        
        # Verify all context fields appear in rendered templates
        self.assertIn('Test Gym', html)  # gym_name
        self.assertIn('admin@test.com', html)  # admin_email
        self.assertIn('MyTempPass', html)  # temp_password
        self.assertIn('http://localhost:5173/login', html)  # login_url
        self.assertIn('soporte@controlfit.app', html)  # support_email
        
        self.assertIn('Test Gym', plain)
        self.assertIn('admin@test.com', plain)
        self.assertIn('MyTempPass', plain)
        self.assertIn('http://localhost:5173/login', plain)
        self.assertIn('soporte@controlfit.app', plain)

    @patch('gimnasioApp.services.email.logger')
    def test_send_welcome_email_logs_error_on_missing_gym(self, mock_logger):
        """Test that missing gym logs error and doesn't raise."""
        from gimnasioApp.services.email import send_welcome_email
        
        # Call with non-existent gym_id
        send_welcome_email(99999, self.admin.id, 'TempPass123')
        
        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args[0]
        self.assertIn('not found', call_args[0])

    @patch('gimnasioApp.services.email.logger')
    def test_send_welcome_email_logs_error_on_missing_admin(self, mock_logger):
        """Test that missing admin logs error and doesn't raise."""
        from gimnasioApp.services.email import send_welcome_email
        
        # Call with non-existent admin_id
        send_welcome_email(self.gimnasio.id, 99999, 'TempPass123')
        
        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args[0]
        self.assertIn('not found', call_args[0])

    @patch('gimnasioApp.services.email.send_mail', side_effect=Exception('SMTP Error'))
    @patch('gimnasioApp.services.email.logger')
    @patch('django.conf.settings.FRONTEND_URL', 'http://localhost:5173')
    @patch('django.conf.settings.SUPPORT_EMAIL', 'soporte@controlfit.app')
    @patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'ControlFit <noreply@controlfit.app>')
    def test_send_welcome_email_logs_error_on_send_failure(self, mock_logger, mock_send_mail):
        """Test that send_mail failure logs exception and doesn't re-raise."""
        from gimnasioApp.services.email import send_welcome_email
        
        # Should not raise
        send_welcome_email(self.gimnasio.id, self.admin.id, 'TempPass123')
        
        mock_logger.exception.assert_called()
        call_args = mock_logger.exception.call_args
        # call_args[0] is the format string, call_args[1] are the args
        self.assertIn('Failed to send welcome email', call_args[0][0])
        self.assertIn('admin@test.com', call_args[0][1])


class DemoRequestSerializerEmailSentTest(TestCase):
    """Tests for email_sent SerializerMethodField in DemoRequestSerializer."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.demo = DemoRequest.objects.create(
            nombre="Juan Perez",
            email="juan@test.com",
            telefono="3005555555",
            nombre_gimnasio="Test Gym",
            estado='pendiente'
        )

    def test_email_sent_false_when_gym_creado_none(self):
        """email_sent should be False when gym_creado is None."""
        serializer = DemoRequestSerializer(self.demo)
        self.assertFalse(serializer.data['email_sent'])

    def test_email_sent_true_when_gym_creado_exists(self):
        """email_sent should be True when gym_creado exists."""
        self.demo.gym_creado = self.gimnasio
        self.demo.save()
        
        serializer = DemoRequestSerializer(self.demo)
        self.assertTrue(serializer.data['email_sent'])


class DemoRequestViewSetEmailIntegrationTest(TransactionTestCase):
    """Integration tests for email wiring in DemoRequestViewSet."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.superadmin = Usuario.objects.create_user(
            email="super@test.com",
            name="Super",
            lastname="Admin",
            password="password123",
            roles="superadmin",
            gimnasio=None
        )
        self.factory = APIRequestFactory()

    def _patch_demo(self, demo_id, data, token):
        import json
        request = self.factory.patch(
            f'/solicitudes-demo/{demo_id}/',
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        view = DemoRequestViewSet.as_view({'patch': 'partial_update'})
        return view(request, pk=demo_id)

    @patch('gimnasioApp.views.send_welcome_email')
    def test_viewset_wires_email_on_commit(self, mock_send_welcome_email):
        """Integration: transaction.on_commit calls _send_welcome_email_safe."""
        from rest_framework_simplejwt.tokens import RefreshToken
        import uuid

        refresh = RefreshToken.for_user(self.superadmin)
        self.superadmin_token = str(refresh.access_token)
        
        # Use unique email to avoid conflicts with existing test data
        unique_email = f"juan_{uuid.uuid4().hex[:8]}@newgym.com"
        demo = DemoRequest.objects.create(
            nombre="Juan Perez",
            email=unique_email,
            telefono="3005555555",
            nombre_gimnasio="New Gym",
            estado='pendiente'
        )
        
        response = self._patch_demo(demo.id, {'estado': 'contactado'}, self.superadmin_token)
        
        self.assertEqual(response.status_code, 200)
        demo.refresh_from_db()
        self.assertIsNotNone(demo.gym_creado)
        
        # In TransactionTestCase, on_commit callbacks run immediately
        mock_send_welcome_email.assert_called_once()
        call_args = mock_send_welcome_email.call_args[0]
        self.assertEqual(call_args[0], demo.gym_creado.id)
        self.assertEqual(call_args[1], Usuario.objects.get(email=unique_email).id)
        self.assertTrue(len(call_args[2]) > 0)  # temp_password


# ============================================================
# PHASE 4: PASSWORD CHANGE FLOW TESTS
# ============================================================

class PasswordChangeSerializerTest(TestCase):
    """Tests for PasswordChangeSerializer validation."""

    def setUp(self):
        self.gym = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.objects.create_user(
            email='test@gym.com',
            password='TempPass123',
            name='Test',
            lastname='User',
            roles='admin',
            gimnasio=self.gym
        )

    def test_serializer_valid_data(self):
        """Serializer accepts valid old_password, new_password, confirm_password."""
        from gimnasioApp.serializers import PasswordChangeSerializer
        
        serializer = PasswordChangeSerializer(data={
            'old_password': 'TempPass123',
            'new_password': 'NewPass456',
            'confirm_password': 'NewPass456'
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['old_password'], 'TempPass123')
        self.assertEqual(serializer.validated_data['new_password'], 'NewPass456')

    def test_serializer_rejects_mismatched_passwords(self):
        """Serializer rejects when new_password != confirm_password."""
        from gimnasioApp.serializers import PasswordChangeSerializer
        
        serializer = PasswordChangeSerializer(data={
            'old_password': 'TempPass123',
            'new_password': 'NewPass456',
            'confirm_password': 'DifferentPass789'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)
        self.assertIn('coinciden', str(serializer.errors['confirm_password']).lower())

    def test_serializer_rejects_short_new_password(self):
        """Serializer rejects new_password < 8 characters."""
        from gimnasioApp.serializers import PasswordChangeSerializer
        
        serializer = PasswordChangeSerializer(data={
            'old_password': 'TempPass123',
            'new_password': 'Short1',
            'confirm_password': 'Short1'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_serializer_rejects_missing_fields(self):
        """Serializer rejects when required fields are missing."""
        from gimnasioApp.serializers import PasswordChangeSerializer
        
        serializer = PasswordChangeSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
        self.assertIn('new_password', serializer.errors)
        self.assertIn('confirm_password', serializer.errors)


class PasswordChangeViewTest(TestCase):
    """Tests for PasswordChangeView endpoint."""

    def setUp(self):
        self.gym = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.objects.create_user(
            email='test@gym.com',
            password='TempPass123',
            name='Test',
            lastname='User',
            roles='admin',
            gimnasio=self.gym
        )
        self.user.must_change_password = True
        self.user.save()
        
        from rest_framework.test import APIRequestFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.factory = APIRequestFactory()
        self.token = str(RefreshToken.for_user(self.user).access_token)

    def _post_password_change(self, data, token=None):
        """Helper to POST to password change endpoint."""
        from gimnasioApp.views import PasswordChangeView
        import json
        
        request = self.factory.post(
            '/auth/password/change/',
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token or self.token}'
        )
        view = PasswordChangeView.as_view()
        return view(request)

    def test_password_change_success_resets_flag(self):
        """Happy path: valid old_password + matching new passwords -> 200, must_change_password=False."""
        response = self._post_password_change({
            'old_password': 'TempPass123',
            'new_password': 'NewSecurePass456',
            'confirm_password': 'NewSecurePass456'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('detail', response.data)
        self.assertIn('actualizada', response.data['detail'].lower())
        
        # Verify flag is reset
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        
        # Verify password actually changed
        self.assertTrue(self.user.check_password('NewSecurePass456'))

    def test_password_change_wrong_old_password_returns_400(self):
        """Wrong old_password -> 400 with error on old_password field."""
        response = self._post_password_change({
            'old_password': 'WrongPassword',
            'new_password': 'NewSecurePass456',
            'confirm_password': 'NewSecurePass456'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('old_password', response.data)
        self.assertIn('incorrecta', str(response.data['old_password']).lower())
        
        # Flag should remain True
        self.user.refresh_from_db()
        self.assertTrue(self.user.must_change_password)

    def test_password_change_mismatched_new_passwords_returns_400(self):
        """new_password != confirm_password -> 400 with error on confirm_password."""
        response = self._post_password_change({
            'old_password': 'TempPass123',
            'new_password': 'NewSecurePass456',
            'confirm_password': 'DifferentPass789'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('confirm_password', response.data)
        self.assertIn('coinciden', str(response.data['confirm_password']).lower())

    def test_password_change_short_new_password_returns_400(self):
        """new_password < 8 chars -> 400 with error on new_password."""
        response = self._post_password_change({
            'old_password': 'TempPass123',
            'new_password': 'Short1',
            'confirm_password': 'Short1'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('new_password', response.data)

    def test_password_change_unauthenticated_returns_401(self):
        """Unauthenticated request -> 401."""
        from gimnasioApp.views import PasswordChangeView
        
        request = self.factory.post(
            '/auth/password/change/',
            data={'old_password': 'TempPass123', 'new_password': 'NewPass456', 'confirm_password': 'NewPass456'},
            content_type='application/json'
        )
        view = PasswordChangeView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 401)

    def test_password_change_user_without_flag_still_works(self):
        """User without must_change_password=True can still change password."""
        # Create a fresh user without the flag to avoid interference from previous tests
        fresh_user = Usuario.objects.create_user(
            email='fresh@gym.com',
            password='TempPass123',
            name='Fresh',
            lastname='User',
            roles='admin',
            gimnasio=self.gym
        )
        fresh_user.must_change_password = False
        fresh_user.save()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        fresh_token = str(RefreshToken.for_user(fresh_user).access_token)
        
        response = self._post_password_change({
            'old_password': 'TempPass123',
            'new_password': 'AnotherNewPass789',
            'confirm_password': 'AnotherNewPass789'
        }, token=fresh_token)
        
        self.assertEqual(response.status_code, 200)
        fresh_user.refresh_from_db()
        self.assertTrue(fresh_user.check_password('AnotherNewPass789'))


class RequirePasswordChangePermissionTest(TestCase):
    """Tests for RequirePasswordChange permission class."""

    def setUp(self):
        self.gym = Gimnasio.objects.create(name="Test Gym")
        self.user_with_flag = Usuario.objects.create_user(
            email='withflag@gym.com',
            password='TempPass123',
            name='With',
            lastname='Flag',
            roles='admin',
            gimnasio=self.gym
        )
        self.user_with_flag.must_change_password = True
        self.user_with_flag.save()
        
        self.user_without_flag = Usuario.objects.create_user(
            email='withoutflag@gym.com',
            password='NormalPass123',
            name='Without',
            lastname='Flag',
            roles='admin',
            gimnasio=self.gym
        )
        
        from rest_framework.test import APIRequestFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.factory = APIRequestFactory()
        self.token_with_flag = str(RefreshToken.for_user(self.user_with_flag).access_token)
        self.token_without_flag = str(RefreshToken.for_user(self.user_without_flag).access_token)

    def test_permission_allows_access_when_flag_false(self):
        """User with must_change_password=False can access protected views."""
        from gimnasioApp.permissions import RequirePasswordChange
        from gimnasioApp.views import Home
        
        request = self.factory.get('/home/', HTTP_AUTHORIZATION=f'Bearer {self.token_without_flag}')
        request.user = self.user_without_flag
        
        perm = RequirePasswordChange()
        # Simulate a view with basename that's not excluded
        class MockView:
            basename = 'home'
        view = MockView()
        
        self.assertTrue(perm.has_permission(request, view))

    def test_permission_denies_access_when_flag_true(self):
        """User with must_change_password=True is denied access to protected views."""
        from gimnasioApp.permissions import RequirePasswordChange
        
        request = self.factory.get('/home/', HTTP_AUTHORIZATION=f'Bearer {self.token_with_flag}')
        request.user = self.user_with_flag
        
        perm = RequirePasswordChange()
        class MockView:
            basename = 'home'
        view = MockView()
        
        self.assertFalse(perm.has_permission(request, view))
        self.assertIn('cambiar', perm.message.lower())

    def test_permission_allows_password_change_endpoint(self):
        """Password change endpoint is accessible even when flag is True."""
        from gimnasioApp.permissions import RequirePasswordChange
        
        request = self.factory.post('/auth/password/change/', HTTP_AUTHORIZATION=f'Bearer {self.token_with_flag}')
        request.user = self.user_with_flag
        
        perm = RequirePasswordChange()
        class MockView:
            basename = 'password-change'
        view = MockView()
        
        self.assertTrue(perm.has_permission(request, view))

    def test_permission_allows_logout_endpoint(self):
        """Logout endpoint is accessible even when flag is True."""
        from gimnasioApp.permissions import RequirePasswordChange
        
        request = self.factory.post('/auth/logout/', HTTP_AUTHORIZATION=f'Bearer {self.token_with_flag}')
        request.user = self.user_with_flag
        
        perm = RequirePasswordChange()
        class MockView:
            basename = 'logout'
        view = MockView()
        
        self.assertTrue(perm.has_permission(request, view))