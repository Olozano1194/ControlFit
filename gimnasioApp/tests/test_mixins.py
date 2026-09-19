"""Tests for MultiTenantViewSetMixin.

Extracted from the original tests.py (lines 73-145).
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from .factories import create_gimnasio, create_user, create_miembro, create_membresia
from gimnasioApp.views import UsuarioGymViewSet, MembresiaViewSet


class MultiTenantViewSetMixinTest(TestCase):
    def setUp(self):
        self.gimnasio1 = create_gimnasio(name="Gym 1")
        self.gimnasio2 = create_gimnasio(name="Gym 2")

        self.user1 = create_user(
            email="user1@example.com",
            name="User",
            lastname="One",
            password="password123",
            gimnasio=self.gimnasio1
        )
        self.user2 = create_user(
            email="user2@example.com",
            name="User",
            lastname="Two",
            password="password123",
            gimnasio=self.gimnasio2
        )

        self.member1 = create_miembro("Member", "One", self.gimnasio1)
        self.member2 = create_miembro("Member", "Two", self.gimnasio2)

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
        create_membresia(self.gimnasio1, name="Plan 1", price=100, duration=30)
        create_membresia(self.gimnasio2, name="Plan 2", price=200, duration=30)

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