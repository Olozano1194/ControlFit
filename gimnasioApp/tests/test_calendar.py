"""Tests for the backend calendar module (TipoEvento + EventoCalendario + Public Endpoint).

Extracted from the calendar-recuperado branch tests.py and adapted to use
the new tests package structure with factories and helpers.
"""

from datetime import timedelta
from django.test import TestCase
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from .factories import (
    create_gimnasio, create_user, create_admin_user, create_tipo_evento,
    create_evento_calendario, _utc_datetime
)
from ..models import TipoEvento, EventoCalendario, DemoRequest, Gimnasio, Usuario
from ..serializers.calendar_serializer import EventoCalendarioSerializer
from ..views.calendar_views import (
    TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView
)


class TipoEventoModelTest(TestCase):
    """Tests del modelo TipoEvento."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym Model")

    def test_create_tipo_evento_sets_fields(self):
        tipo = create_tipo_evento(self.gimnasio, nombre="Clase", color="#FF0000")
        self.assertEqual(tipo.nombre, "Clase")
        self.assertEqual(tipo.color, "#FF0000")
        self.assertEqual(tipo.gimnasio, self.gimnasio)
        self.assertIsNotNone(tipo.created_at)

    def test_ordering_by_nombre(self):
        create_tipo_evento(self.gimnasio, nombre="Zumba", color="#00FF00")
        create_tipo_evento(self.gimnasio, nombre="Clase", color="#FF0000")
        tipos = list(TipoEvento.objects.filter(gimnasio=self.gimnasio))
        self.assertEqual([t.nombre for t in tipos], ["Clase", "Zumba"])

    def test_tipo_evento_isolated_by_gimnasio(self):
        gym2 = create_gimnasio(name="Gym 2")
        create_tipo_evento(self.gimnasio, nombre="A", color="#000000")
        create_tipo_evento(gym2, nombre="B", color="#111111")
        self.assertEqual(TipoEvento.objects.filter(gimnasio=self.gimnasio).count(), 1)
        self.assertEqual(TipoEvento.objects.filter(gimnasio=gym2).count(), 1)


class EventoCalendarioModelTest(TestCase):
    """Tests del modelo EventoCalendario."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym Model")
        self.tipo = create_tipo_evento(self.gimnasio, nombre="Clase", color="#FF0000")
        self.user = create_admin_user(self.gimnasio)
        self.user.email = "cal-model@example.com"
        self.user.name = "Cal"
        self.user.lastname = "Model"
        self.user.save()

    def test_create_evento_with_tipo_and_created_by(self):
        evento = create_evento_calendario(
            gimnasio=self.gimnasio,
            titulo="Yoga",
            fecha_inicio=_utc_datetime(2026, 8, 15, 10, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 12, 0),
            tipo=self.tipo,
            created_by=self.user,
        )
        self.assertEqual(evento.titulo, "Yoga")
        self.assertEqual(evento.tipo, self.tipo)
        self.assertEqual(evento.created_by, self.user)
        self.assertEqual(evento.descripcion, "")
        self.assertIsNone(evento.relacion_id)

    def test_create_evento_with_null_optionals(self):
        evento = create_evento_calendario(
            gimnasio=self.gimnasio,
            titulo="Reuni\u00f3n",
            fecha_inicio=_utc_datetime(2026, 8, 16, 9, 0),
            fecha_fin=_utc_datetime(2026, 8, 16, 10, 0),
            tipo=None,
            created_by=None,
            descripcion="",
            relacion_tipo=None,
            relacion_id=None,
        )
        self.assertIsNone(evento.tipo)
        self.assertIsNone(evento.relacion_tipo)
        self.assertIsNone(evento.relacion_id)
        self.assertIsNone(evento.created_by)


class TipoEventoViewSetTest(TestCase):
    """Tests del viewset TipoEvento: CRUD admin-only y aislamiento multi-tenant."""

    def setUp(self):
        self.gimnasio1 = create_gimnasio(name="Gym 1")
        self.gimnasio2 = create_gimnasio(name="Gym 2")
        self.admin1 = create_admin_user(self.gimnasio1)
        self.admin1.email = "admin1@example.com"
        self.admin1.save()
        self.admin2 = create_admin_user(self.gimnasio2)
        self.admin2.email = "admin2@example.com"
        self.admin2.save()
        self.recepcion1 = create_user(
            email="rec1@example.com", name="R", lastname="One",
            password="password123", gimnasio=self.gimnasio1, roles="recepcion"
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
            create_tipo_evento(self.gimnasio1, nombre=f"Tipo G1 {i}", color="#000000")
        for i in range(2):
            create_tipo_evento(self.gimnasio2, nombre=f"Tipo G2 {i}", color="#111111")
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
        tipo_g1 = create_tipo_evento(self.gimnasio1, nombre="G1 Only", color="#000000")
        view = TipoEventoViewSet.as_view({'put': 'update'})
        request = self.factory.put('/', {'nombre': 'Hacked', 'color': '#FFFFFF'}, format='json')
        request.user = self.admin2
        request.gimnasio = self.gimnasio2
        force_authenticate(request, user=self.admin2)
        response = view(request, pk=tipo_g1.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_removes_tipo(self):
        tipo = create_tipo_evento(self.gimnasio1, nombre="Delete Me", color="#000000")
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
        self.gimnasio1 = create_gimnasio(name="Gym 1")
        self.gimnasio2 = create_gimnasio(name="Gym 2")
        self.recepcion1 = create_user(
            email="rec1@example.com", name="R", lastname="One",
            password="password123", gimnasio=self.gimnasio1, roles="recepcion"
        )
        self.user2 = create_user(
            email="user2@example.com", name="U", lastname="Two",
            password="password123", gimnasio=self.gimnasio2, roles="admin"
        )
        self.tipo = create_tipo_evento(self.gimnasio1, nombre="Clase", color="#FF0000")
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
        evento = create_evento_calendario(
            gimnasio=self.gimnasio1,
            titulo="Yoga",
            fecha_inicio=_utc_datetime(2026, 8, 15, 10, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 12, 0),
            tipo=self.tipo,
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
        evento = create_evento_calendario(
            gimnasio=self.gimnasio1,
            titulo="Sin Tipo",
            fecha_inicio=_utc_datetime(2026, 8, 15, 10, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 12, 0),
            tipo=None,
        )
        serializer = EventoCalendarioSerializer(evento)
        self.assertIsNone(serializer.data['tipo_detalle'])

    def test_create_with_optional_fields_null(self):
        view = EventoCalendarioViewSet.as_view({'post': 'create'})
        data = {
            'titulo': 'Reuni\u00f3n',
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
            create_evento_calendario(
                gimnasio=self.gimnasio1,
                titulo=f"E1-{i}",
                fecha_inicio=_utc_datetime(2026, 8, 15, 8, 0),
                fecha_fin=_utc_datetime(2026, 8, 15, 9, 0),
            )
        for i in range(2):
            create_evento_calendario(
                gimnasio=self.gimnasio2,
                titulo=f"E2-{i}",
                fecha_inicio=_utc_datetime(2026, 8, 15, 8, 0),
                fecha_fin=_utc_datetime(2026, 8, 15, 9, 0),
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
        evento = create_evento_calendario(
            gimnasio=self.gimnasio1,
            titulo='Original',
            descripcion='keep me',
            fecha_inicio=_utc_datetime(2026, 8, 15, 8, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 9, 0),
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
    """Tests del filtro de rango con sem\u00e1ntica de overlap (?start=&end=)."""

    def setUp(self):
        self.gimnasio = create_gimnasio(name="Gym 1")
        self.user = create_user(
            email="rec@example.com", name="R", lastname="One",
            password="password123", gimnasio=self.gimnasio, roles="recepcion"
        )
        self.factory = APIRequestFactory()
        # E3: 07:00-09:00 ; E1: 08:00-10:00 ; E2: 09:00-11:00
        self.e3 = create_evento_calendario(
            gimnasio=self.gimnasio,
            titulo="E3", fecha_inicio=_utc_datetime(2026, 8, 15, 7, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 9, 0),
        )
        self.e1 = create_evento_calendario(
            gimnasio=self.gimnasio,
            titulo="E1", fecha_inicio=_utc_datetime(2026, 8, 15, 8, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 10, 0),
        )
        self.e2 = create_evento_calendario(
            gimnasio=self.gimnasio,
            titulo="E2", fecha_inicio=_utc_datetime(2026, 8, 15, 9, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 11, 0),
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
    """Tests del endpoint p\u00fablico GET /api/calendario/publico/{gimnasio_id}/."""

    def setUp(self):
        self.gimnasio1 = create_gimnasio(name="Gym 1")
        self.gimnasio2 = create_gimnasio(name="Gym 2")
        self.tipo = create_tipo_evento(self.gimnasio1, nombre="Clase", color="#FF0000")

    def test_valid_gym_returns_events_ordered_with_tipo_detalle(self):
        create_evento_calendario(
            gimnasio=self.gimnasio1,
            titulo="A", fecha_inicio=_utc_datetime(2026, 8, 15, 8, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 9, 0),
        )
        create_evento_calendario(
            gimnasio=self.gimnasio1,
            titulo="B", fecha_inicio=_utc_datetime(2026, 8, 15, 7, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 8, 0),
            tipo=self.tipo,
        )
        create_evento_calendario(
            gimnasio=self.gimnasio2,
            titulo="Other", fecha_inicio=_utc_datetime(2026, 8, 15, 9, 0),
            fecha_fin=_utc_datetime(2026, 8, 15, 10, 0),
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
        match = resolve(f'/api/calendario/publico/{self.gimnasio1.id}/')
        self.assertEqual(match.func.cls.__name__, 'PublicCalendarioView')
        self.assertFalse(match.route.startswith('gym/api/v1'))