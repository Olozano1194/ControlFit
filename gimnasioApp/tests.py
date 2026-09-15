import io
import base64
import json
import requests
from django.test import TestCase, TransactionTestCase
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from unittest.mock import patch, MagicMock, call

from decimal import Decimal
from datetime import timedelta, date
from .models import Gimnasio, Usuario, UsuarioGym, Membresia, MembresiaAsignada, PagoMembresia
from .middleware import GimnasioMiddleware
from .mixins import MultiTenantViewSetMixin
from .serializers import UsuarioSerializer, UsuarioGymSerializer, MembresiasSerializer, MembresiaAsignadaSerializer, PagoMembresiaSerializer
from .views import UserViewSet, UsuarioGymViewSet, MembresiaViewSet, Home, PagoMembresiaViewSet
from .storage import SupabaseMediaStorage
from django.core.files.uploadedfile import SimpleUploadedFile


class GimnasioMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = GimnasioMiddleware(lambda r: None)

    def test_authenticated_user_gets_gimnasio(self):
        gimnasio = Gimnasio.objects.create(name="Test Gym")
        user = Usuario.all_objects.create_user(
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
        user = Usuario.all_objects.create_user(
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

        self.user1 = Usuario.all_objects.create_user(
            email="user1@example.com",
            name="User",
            lastname="One",
            password="password123",
            gimnasio=self.gimnasio1
        )
        self.user2 = Usuario.all_objects.create_user(
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
        self.admin = Usuario.all_objects.create_user(
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
        self.user = Usuario.all_objects.create_user(
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
        self.user = Usuario.all_objects.create_user(
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
        user = Usuario.all_objects.create_user(
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
        user = Usuario.all_objects.create_user(
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
        user = Usuario.all_objects.create_user(
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
        self.user = Usuario.all_objects.create_user(
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
        self.user = Usuario.all_objects.create_user(
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
# EMAIL SERVICE TESTS (Fixed for Resend API)
# ============================================================

class EmailServiceTest(TestCase):
    """Unit tests for send_welcome_email service."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.admin = Usuario.all_objects.create_user(
            email="admin@test.com",
            name="Admin",
            lastname="User",
            password="password123",
            roles="admin",
            gimnasio=self.gimnasio
        )

    @patch('gimnasioApp.services.email.requests.post')
    @patch('django.conf.settings.FRONTEND_URL', 'http://localhost:5173')
    @patch('django.conf.settings.SUPPORT_EMAIL', 'soporte@controlfit.app')
    @patch('django.conf.settings.RESEND_API_KEY', 're_test_key')
    @patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'ControlFit <noreply@controlfit.app>')
    def test_send_welcome_email_renders_templates(self, mock_post):
        """Test that send_welcome_email renders both HTML and text templates via Resend API."""
        from gimnasioApp.services.email import send_welcome_email
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        send_welcome_email(self.gimnasio.id, self.admin.id, 'TempPass123')
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify Resend API URL
        self.assertEqual(call_args.args[0], "https://api.resend.com/emails")
        
        # Verify payload structure
        payload = call_args.kwargs['json']
        self.assertIn('from', payload)
        self.assertIn('to', payload)
        self.assertIn('subject', payload)
        self.assertIn('html', payload)
        self.assertIn('text', payload)
        
        # Verify subject
        self.assertIn('Bienvenido a ControlFit', payload['subject'])
        self.assertIn('Test Gym', payload['subject'])
        
        # Verify recipient
        self.assertEqual(payload['to'], ['admin@test.com'])
        
        # Verify from email
        self.assertEqual(payload['from'], 'ControlFit <noreply@controlfit.app>')
        
        # Verify html and text content exist
        self.assertTrue(len(payload['html']) > 0)
        self.assertTrue(len(payload['text']) > 0)
        
        # Verify content includes key data
        html = payload['html']
        plain = payload['text']
        self.assertIn('Test Gym', html)
        self.assertIn('admin@test.com', html)
        self.assertIn('TempPass123', html)
        self.assertIn('http://localhost:5173/login', html)
        self.assertIn('soporte@controlfit.app', html)
        self.assertIn('Test Gym', plain)
        self.assertIn('admin@test.com', plain)
        self.assertIn('TempPass123', plain)
        self.assertIn('http://localhost:5173/login', plain)
        self.assertIn('soporte@controlfit.app', plain)

    @patch('gimnasioApp.services.email.requests.post')
    @patch('django.conf.settings.FRONTEND_URL', 'http://localhost:5173')
    @patch('django.conf.settings.SUPPORT_EMAIL', 'soporte@controlfit.app')
    @patch('django.conf.settings.RESEND_API_KEY', 're_test_key')
    @patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'ControlFit <noreply@controlfit.app>')
    def test_send_welcome_email_context_includes_all_fields(self, mock_post):
        """Test that template context includes all required fields."""
        from gimnasioApp.services.email import send_welcome_email
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        send_welcome_email(self.gimnasio.id, self.admin.id, 'MyTempPass')
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        html = payload['html']
        plain = payload['text']
        
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


# ============================================================
# JWT TOKEN LIFETIME TESTS (Phase 1)
# ============================================================

class TokenLifetimeSettingsTest(TestCase):
    """Tests for SIMPLE_JWT token lifetime configuration."""

    def test_access_token_lifetime_is_15_minutes(self):
        """SIMPLE_JWT ACCESS_TOKEN_LIFETIME should be 15 minutes."""
        from django.conf import settings
        from datetime import timedelta
        
        self.assertEqual(
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            timedelta(minutes=15)
        )

    def test_refresh_token_lifetime_is_3_days(self):
        """SIMPLE_JWT REFRESH_TOKEN_LIFETIME should be 3 days (72 hours)."""
        from django.conf import settings
        from datetime import timedelta
        
        self.assertEqual(
            settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
            timedelta(days=3)
        )

    def test_rotate_refresh_tokens_enabled(self):
        """SIMPLE_JWT ROTATE_REFRESH_TOKENS should be True."""
        from django.conf import settings
        
        self.assertTrue(settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS'])

    def test_blacklist_after_rotation_enabled(self):
        """SIMPLE_JWT BLACKLIST_AFTER_ROTATION should be True."""
        from django.conf import settings
        
        self.assertTrue(settings.SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'])


class CSRFSettingTest(TestCase):
    """Tests for CSRF_ENFORCE feature flag."""

    def test_csrf_enforce_is_enabled(self):
        """CSRF_ENFORCE should be True (enforce mode enabled)."""
        from django.conf import settings
        
        self.assertTrue(settings.CSRF_ENFORCE)


# ============================================================
# PHASE 2: CSRF COOKIE HELPERS TESTS
# ============================================================

class CSRFCookieHelperTest(TestCase):
    """Tests for CSRF cookie helper functions in auth_cookie.py."""

    def setUp(self):
        from django.http import HttpResponse
        self.response = HttpResponse()

    def test_set_csrf_cookie_sets_correct_attributes_in_development(self):
        """set_csrf_cookie should set cookie with HttpOnly=False, SameSite=Lax, correct path in DEBUG=True."""
        from django.test.utils import override_settings
        from gimnasioApp.auth_cookie import set_csrf_cookie
        
        with override_settings(DEBUG=True):
            set_csrf_cookie(self.response, 'test-csrf-token')
            
            cookie = self.response.cookies.get('csrftoken')
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, 'test-csrf-token')
            self.assertFalse(cookie['httponly'])  # HttpOnly=False for JS access
            self.assertEqual(cookie['samesite'], 'Lax')  # SameSite=Lax in dev
            self.assertEqual(cookie['path'], '/')  # Root path for JS access from any frontend route
            self.assertEqual(cookie['max-age'], 86400)  # 1 day
            self.assertFalse(cookie['secure'])  # Not secure in dev

    def test_set_csrf_cookie_sets_correct_attributes_in_production(self):
        """set_csrf_cookie should set cookie with Secure=True, SameSite=None in DEBUG=False."""
        from django.test.utils import override_settings
        from gimnasioApp.auth_cookie import set_csrf_cookie
        
        with override_settings(DEBUG=False):
            set_csrf_cookie(self.response, 'prod-csrf-token')
            
            cookie = self.response.cookies.get('csrftoken')
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, 'prod-csrf-token')
            self.assertFalse(cookie['httponly'])  # HttpOnly=False for JS access
            self.assertEqual(cookie['samesite'], 'None')  # SameSite=None in prod
            self.assertEqual(cookie['path'], '/')  # Root path for JS access from any frontend route
            self.assertEqual(cookie['max-age'], 86400)  # 1 day
            self.assertTrue(cookie['secure'])  # Secure in prod

    def test_clear_csrf_cookie_clears_with_correct_attributes(self):
        """clear_csrf_cookie should delete cookie with matching path and SameSite."""
        from django.test.utils import override_settings
        from gimnasioApp.auth_cookie import clear_csrf_cookie
        
        with override_settings(DEBUG=True):
            clear_csrf_cookie(self.response)
            
            cookie = self.response.cookies.get('csrftoken')
            self.assertIsNotNone(cookie)
            self.assertEqual(cookie.value, '')  # Empty value for deletion
            self.assertEqual(cookie['path'], '/')
            self.assertEqual(cookie['samesite'], 'Lax')

    def test_get_csrf_token_returns_token_from_request(self):
        """get_csrf_token should extract csrftoken from request cookies."""
        from django.test import RequestFactory
        from gimnasioApp.auth_cookie import get_csrf_token
        
        factory = RequestFactory()
        request = factory.get('/')
        request.COOKIES['csrftoken'] = 'extracted-token'
        
        token = get_csrf_token(request)
        self.assertEqual(token, 'extracted-token')

    def test_get_csrf_token_returns_none_when_missing(self):
        """get_csrf_token should return None when cookie is not present."""
        from django.test import RequestFactory
        from gimnasioApp.auth_cookie import get_csrf_token
        
        factory = RequestFactory()
        request = factory.get('/')
        # No csrftoken cookie set
        
        token = get_csrf_token(request)
        self.assertIsNone(token)


# ============================================================
# PHASE 2: CSRF VALIDATION TESTS
# ============================================================

class CSRFValidationTest(TestCase):
    """Tests for validate_csrf function with log-only mode."""

    def setUp(self):
        from django.test import RequestFactory
        self.factory = RequestFactory()

    def _make_request(self, method='POST', csrf_header=None, csrf_cookie=None):
        """Helper to create a request with optional CSRF header and cookie."""
        request = self.factory.generic(method, '/gym/api/v1/some-endpoint/')
        if csrf_header:
            request.META['HTTP_X_CSRF_TOKEN'] = csrf_header
        if csrf_cookie:
            request.COOKIES['csrftoken'] = csrf_cookie
        return request

    @patch('django.conf.settings.CSRF_ENFORCE', False)
    @patch('gimnasioApp.views.logger')
    def test_validate_csrf_log_only_mode_allows_missing_header(self, mock_logger):
        """In log-only mode (CSRF_ENFORCE=False), missing header should log but return True."""
        from gimnasioApp.views import validate_csrf
        
        request = self._make_request(method='POST', csrf_cookie='valid-token')
        result = validate_csrf(request)
        
        self.assertTrue(result)
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0]
        self.assertIn('CSRF validation failed', call_args[0])

    @patch('django.conf.settings.CSRF_ENFORCE', False)
    @patch('gimnasioApp.views.logger')
    def test_validate_csrf_log_only_mode_allows_mismatched_header(self, mock_logger):
        """In log-only mode, mismatched header should log but return True."""
        from gimnasioApp.views import validate_csrf
        
        request = self._make_request(method='POST', csrf_header='wrong-token', csrf_cookie='valid-token')
        result = validate_csrf(request)
        
        self.assertTrue(result)
        mock_logger.warning.assert_called()

    @patch('django.conf.settings.CSRF_ENFORCE', True)
    def test_validate_csrf_enforce_mode_rejects_missing_header(self):
        """In enforce mode (CSRF_ENFORCE=True), missing header should return False."""
        from gimnasioApp.views import validate_csrf
        
        request = self._make_request(method='POST', csrf_cookie='valid-token')
        result = validate_csrf(request)
        
        self.assertFalse(result)

    @patch('django.conf.settings.CSRF_ENFORCE', True)
    def test_validate_csrf_enforce_mode_rejects_mismatched_header(self):
        """In enforce mode, mismatched header should return False."""
        from gimnasioApp.views import validate_csrf
        
        request = self._make_request(method='POST', csrf_header='wrong-token', csrf_cookie='valid-token')
        result = validate_csrf(request)
        
        self.assertFalse(result)

    @patch('django.conf.settings.CSRF_ENFORCE', True)
    def test_validate_csrf_enforce_mode_allows_matching_header(self):
        """In enforce mode, matching header should return True."""
        from gimnasioApp.views import validate_csrf
        
        request = self._make_request(method='POST', csrf_header='matching-token', csrf_cookie='matching-token')
        result = validate_csrf(request)
        
        self.assertTrue(result)

    def test_validate_csrf_get_request_bypasses_validation(self):
        """GET requests should bypass CSRF validation entirely."""
        from gimnasioApp.views import validate_csrf
        
        request = self._make_request(method='GET', csrf_header=None, csrf_cookie=None)
        result = validate_csrf(request)
        
        self.assertTrue(result)

    def test_validate_csrf_put_patch_delete_require_validation(self):
        """PUT, PATCH, DELETE should require CSRF validation."""
        from gimnasioApp.views import validate_csrf
        
        for method in ['PUT', 'PATCH', 'DELETE']:
            with self.subTest(method=method):
                with patch('django.conf.settings.CSRF_ENFORCE', True):
                    request = self._make_request(method=method, csrf_header='token', csrf_cookie='token')
                    result = validate_csrf(request)
                    self.assertTrue(result)
                
                with patch('django.conf.settings.CSRF_ENFORCE', True):
                    request = self._make_request(method=method, csrf_header=None, csrf_cookie='token')
                    result = validate_csrf(request)
                    self.assertFalse(result)


# ============================================================
# PHASE 2: LOGIN/REFRESH/LOGOUT CSRF COOKIE TESTS
# ============================================================

class AuthViewsCSRFCookieTest(TestCase):
    """Tests for CSRF cookie being set/cleared on login, refresh, logout."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def test_login_sets_csrf_cookie(self):
        """POST /token/ should set csrftoken cookie with correct attributes."""
        from gimnasioApp.views import CookieTokenObtainPairView
        
        request = self.factory.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        
        view = CookieTokenObtainPairView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertFalse(cookie['httponly'])
        self.assertEqual(cookie['path'], '/')
        self.assertEqual(cookie['max-age'], 86400)

    def test_refresh_sets_csrf_cookie(self):
        """POST /token/refresh/ should set csrftoken cookie with correct attributes."""
        from gimnasioApp.views import CookieTokenRefreshView
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(self.user)
        
        request = self.factory.post('/gym/api/v1/token/refresh/')
        request.COOKIES['refresh_token'] = str(refresh)
        
        view = CookieTokenRefreshView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertFalse(cookie['httponly'])
        self.assertEqual(cookie['path'], '/')

    def test_logout_clears_csrf_cookie(self):
        """POST /auth/logout/ should clear csrftoken cookie."""
        from gimnasioApp.views import LogoutView
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(self.user)
        
        request = self.factory.post('/gym/api/v1/auth/logout/')
        request.COOKIES['refresh_token'] = str(refresh)
        
        view = LogoutView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertEqual(cookie.value, '')  # Empty for deletion
        self.assertEqual(cookie['path'], '/')

    def test_register_sets_csrf_cookie(self):
        """POST /register/ should set csrftoken cookie with correct attributes."""
        from gimnasioApp.views import RegisterViewSet
        
        request = self.factory.post('/gym/api/v1/register/', {
            'email': 'newuser@example.com',
            'password': 'password123',
            'name': 'New',
            'lastname': 'User'
        }, format='json')
        
        view = RegisterViewSet.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('csrftoken', response.cookies)
        cookie = response.cookies['csrftoken']
        self.assertFalse(cookie['httponly'])
        self.assertEqual(cookie['path'], '/')
        self.assertEqual(cookie['max-age'], 86400)


# ============================================================
# PHASE 3: TOKEN VERIFY ENDPOINT TESTS
# ============================================================

class TokenVerifyEndpointTest(TestCase):
    """Tests for POST /token/verify/ endpoint."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def _make_verify_request(self, auth_header=None):
        """Helper to create a verify request with optional Authorization header."""
        request = self.factory.post('/gym/api/v1/token/verify/')
        if auth_header:
            request.META['HTTP_AUTHORIZATION'] = auth_header
        return request

    def test_verify_valid_token_returns_200_with_valid_and_exp(self):
        """Valid access token → 200 {valid: true, exp: timestamp}."""
        from gimnasioApp.views import CookieTokenVerifyView
        from rest_framework_simplejwt.tokens import AccessToken
        
        access = AccessToken.for_user(self.user)
        auth_header = f'Bearer {access}'
        
        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertTrue(response.data['valid'])
        self.assertIn('exp', response.data)
        self.assertIsInstance(response.data['exp'], int)
        # exp should be a Unix timestamp in the future
        import time
        self.assertGreater(response.data['exp'], int(time.time()))

    def test_verify_expired_token_returns_401(self):
        """Expired access token → 401."""
        from gimnasioApp.views import CookieTokenVerifyView
        from rest_framework_simplejwt.tokens import AccessToken
        from datetime import timedelta
        from django.utils import timezone
        
        # Create an already-expired token by manipulating exp
        access = AccessToken.for_user(self.user)
        # Manually set exp to past
        access.payload['exp'] = int((timezone.now() - timedelta(minutes=10)).timestamp())
        
        auth_header = f'Bearer {access}'
        
        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_invalid_malformed_token_returns_401(self):
        """Invalid/malformed token → 401."""
        from gimnasioApp.views import CookieTokenVerifyView
        
        auth_header = 'Bearer invalid.token.string'
        
        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_missing_authorization_header_returns_401(self):
        """Missing Authorization header → 401."""
        from gimnasioApp.views import CookieTokenVerifyView
        
        request = self._make_verify_request(auth_header=None)
        view = CookieTokenVerifyView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_without_bearer_prefix_returns_401(self):
        """Authorization header without Bearer prefix → 401."""
        from gimnasioApp.views import CookieTokenVerifyView
        from rest_framework_simplejwt.tokens import AccessToken
        
        access = AccessToken.for_user(self.user)
        auth_header = str(access)  # Missing "Bearer " prefix
        
        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_refresh_token_rejected(self):
        """Refresh token passed to verify endpoint → 401 (verify only accepts access tokens)."""
        from gimnasioApp.views import CookieTokenVerifyView
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(self.user)
        auth_header = f'Bearer {refresh}'
        
        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_old_long_lived_token_still_valid(self):
        """Backward compat: token issued with old 30min lifetime still verifies.
        
        Simulates a token created before the config change (old ACCESS_TOKEN_LIFETIME=30min).
        The verify endpoint should accept any valid, non-expired token regardless of
        which config was active when it was issued.
        """
        from gimnasioApp.views import CookieTokenVerifyView
        from rest_framework_simplejwt.tokens import AccessToken
        from datetime import timedelta
        from django.utils import timezone
        
        # Create a token with exp = now + 25 minutes (valid under old 30min config)
        access = AccessToken.for_user(self.user)
        access.payload['exp'] = int((timezone.now() + timedelta(minutes=25)).timestamp())
        
        auth_header = f'Bearer {access}'
        
        request = self._make_verify_request(auth_header)
        view = CookieTokenVerifyView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertTrue(response.data['valid'])
        self.assertIn('exp', response.data)


class TokenVerifyIntegrationTest(TestCase):
    """Integration tests for token verify flow."""

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )
        self.factory = APIRequestFactory()

    def test_login_then_verify_access_token_returns_200(self):
        """Integration: login → get access → call verify → 200."""
        from gimnasioApp.views import CookieTokenObtainPairView, CookieTokenVerifyView
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Step 1: Login
        login_request = self.factory.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        login_view = CookieTokenObtainPairView.as_view()
        login_response = login_view(login_request)
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        access_token = login_response.data['access']
        
        # Step 2: Call verify with the access token
        verify_request = self.factory.post('/gym/api/v1/token/verify/')
        verify_request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        verify_view = CookieTokenVerifyView.as_view()
        verify_response = verify_view(verify_request)
        
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['valid'])
        self.assertIn('exp', verify_response.data)

    def test_refresh_flow_does_not_affect_verify(self):
        """Refresh flow doesn't affect verify (verify uses access token, not refresh)."""
        from gimnasioApp.views import CookieTokenObtainPairView, CookieTokenRefreshView, CookieTokenVerifyView
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Step 1: Login to get initial tokens
        login_request = self.factory.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        login_view = CookieTokenObtainPairView.as_view()
        login_response = login_view(login_request)
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        initial_access = login_response.data['access']
        refresh_cookie = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(refresh_cookie)
        
        # Step 2: Verify initial access token works
        verify_request = self.factory.post('/gym/api/v1/token/verify/')
        verify_request.META['HTTP_AUTHORIZATION'] = f'Bearer {initial_access}'
        verify_view = CookieTokenVerifyView.as_view()
        verify_response = verify_view(verify_request)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['valid'])
        
        # Step 3: Call refresh (rotates refresh token, returns new access)
        refresh_request = self.factory.post('/gym/api/v1/token/refresh/')
        refresh_request.COOKIES['refresh_token'] = refresh_cookie.value
        refresh_view = CookieTokenRefreshView.as_view()
        refresh_response = refresh_view(refresh_request)
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        new_access = refresh_response.data['access']
        
        # Step 4: Verify NEW access token works
        verify_request2 = self.factory.post('/gym/api/v1/token/verify/')
        verify_request2.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access}'
        verify_response2 = verify_view(verify_request2)
        self.assertEqual(verify_response2.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response2.data['valid'])
        
        # Step 5: Verify OLD access token still works (until expiry)
        verify_request3 = self.factory.post('/gym/api/v1/token/verify/')
        verify_request3.META['HTTP_AUTHORIZATION'] = f'Bearer {initial_access}'
        verify_response3 = verify_view(verify_request3)
        self.assertEqual(verify_response3.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response3.data['valid'])


# ============================================================
# PHASE 5: CSRF ENFORCEMENT INTEGRATION TESTS
# ============================================================

class CSRFEnforcementIntegrationTest(TestCase):
    """Integration tests for CSRF enforcement at endpoint level (CSRF_ENFORCE=True).
    
    Uses Django test client (self.client) which runs through the full middleware stack.
    """

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )

    def _login_and_get_tokens(self):
        """Helper: login via test client and return access token, refresh cookie, csrf cookie."""
        login_response = self.client.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        refresh_cookie = login_response.cookies.get('refresh_token')
        csrf_cookie = login_response.cookies.get('csrftoken')
        
        return access_token, refresh_cookie.value if refresh_cookie else None, csrf_cookie.value if csrf_cookie else None

    def test_csrf_missing_header_returns_403(self):
        """POST mutating request without X-CSRF-Token header → 403."""
        access_token, _, csrf_token = self._login_and_get_tokens()
        
        # Make a mutating request WITHOUT X-CSRF-Token header
        response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'New', 'lastname': 'Member'
        }, format='json', HTTP_AUTHORIZATION=f'Bearer {access_token}')
        # No HTTP_X_CSRF_TOKEN header
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csrf_invalid_header_returns_403(self):
        """POST mutating request with mismatched X-CSRF-Token header → 403."""
        access_token, _, csrf_token = self._login_and_get_tokens()
        
        # Make a mutating request with WRONG X-CSRF-Token header
        response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'New', 'lastname': 'Member'
        }, format='json', 
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN='wrong-token')  # Mismatched
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csrf_valid_header_allows_request(self):
        """POST mutating request with matching X-CSRF-Token header → 201."""
        access_token, _, csrf_token = self._login_and_get_tokens()
        
        # Make a mutating request with CORRECT X-CSRF-Token header
        # The test client automatically sends cookies from previous responses
        response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'New', 'lastname': 'Member', 'phone': '3001234567', 'address': 'Calle 123'
        }, format='json', 
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN=csrf_token)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_request_bypasses_csrf(self):
        """GET requests should bypass CSRF validation even without header."""
        access_token, _, _ = self._login_and_get_tokens()
        
        # GET request without X-CSRF-Token header
        response = self.client.get('/gym/api/v1/UserGym/', 
        HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_patch_delete_require_csrf(self):
        """PUT, PATCH, DELETE should require CSRF validation."""
        access_token, _, csrf_token = self._login_and_get_tokens()
        
        # First create a member to update/delete
        create_response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'ToUpdate', 'lastname': 'Member', 'phone': '3001234567', 'address': 'Calle 123'
        }, format='json', 
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN=csrf_token)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        member_id = create_response.data['id']
        
        for method in ['put', 'patch', 'delete']:
            with self.subTest(method=method):
                # Request WITHOUT CSRF token
                if method == 'delete':
                    response = self.client.delete(f'/gym/api/v1/UserGym/{member_id}/', 
                    HTTP_AUTHORIZATION=f'Bearer {access_token}')
                else:
                    response = getattr(self.client, method)(f'/gym/api/v1/UserGym/{member_id}/', {
                        'name': 'Updated', 'lastname': 'Member'
                    }, format='json', HTTP_AUTHORIZATION=f'Bearer {access_token}')
                
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, 
                               f"{method.upper()} without CSRF should return 403")


class FullAuthFlowIntegrationTest(TestCase):
    """Integration test: full login → mutate → refresh flow (task 5.6).
    
    Uses Django test client (self.client) which runs through the full middleware stack.
    """

    def setUp(self):
        self.gimnasio = Gimnasio.objects.create(name="Test Gym")
        self.user = Usuario.all_objects.create_user(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="password123",
            gimnasio=self.gimnasio
        )

    def test_full_login_mutate_refresh_flow(self):
        """Full flow: login → create member (mutate) → refresh → verify token still works."""
        from gimnasioApp.views import CookieTokenVerifyView
        
        # Step 1: Login
        login_response = self.client.post('/gym/api/v1/token/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        refresh_cookie = login_response.cookies.get('refresh_token')
        csrf_token = login_response.cookies.get('csrftoken')
        self.assertIsNotNone(refresh_cookie)
        self.assertIsNotNone(csrf_token)
        
        # Step 2: Verify initial access token
        verify_response = self.client.post('/gym/api/v1/token/verify/', 
        HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['valid'])
        
        # Step 3: Mutating request with CSRF (create member)
        create_response = self.client.post('/gym/api/v1/UserGym/', {
            'name': 'Integration', 'lastname': 'Test', 'phone': '3001234567', 'address': 'Calle 123'
        }, format='json', 
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_CSRF_TOKEN=csrf_token.value)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        member_id = create_response.data['id']
        
        # Step 4: Refresh access token
        refresh_response = self.client.post('/gym/api/v1/token/refresh/', 
        HTTP_COOKIE=f'refresh_token={refresh_cookie.value}')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        new_access = refresh_response.data['access']
        new_csrf_token = refresh_response.cookies.get('csrftoken')
        self.assertIsNotNone(new_csrf_token)
        
        # Step 5: Verify NEW access token works
        verify_response2 = self.client.post('/gym/api/v1/token/verify/', 
        HTTP_AUTHORIZATION=f'Bearer {new_access}')
        self.assertEqual(verify_response2.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response2.data['valid'])
        
        # Step 6: Mutating request with NEW CSRF token (update member)
        update_response = self.client.patch(f'/gym/api/v1/UserGym/{member_id}/', {
            'name': 'Updated'
        }, format='json', content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {new_access}',
        HTTP_X_CSRF_TOKEN=new_csrf_token.value)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['name'], 'Updated')
        
        # Step 7: Verify token verify still works after mutation
        verify_response3 = self.client.post('/gym/api/v1/token/verify/', 
        HTTP_AUTHORIZATION=f'Bearer {new_access}')
        self.assertEqual(verify_response3.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response3.data['valid'])
