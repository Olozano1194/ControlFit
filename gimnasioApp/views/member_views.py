from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from ..serializers import UsuarioSerializer, UsuarioGymSerializer, UsuarioGymDaySerializer
from ..models import Usuario, UsuarioGym, UsuarioGymDay
from ..permissions import IsAdminUser, IsRecepcionUser, RequirePasswordChange
from ..mixins import MultiTenantViewSetMixin


# ============================================================
# USER MANAGEMENT (Admin only)
# ============================================================

class UserViewSet(MultiTenantViewSetMixin, viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, RequirePasswordChange]  # Solo admins pueden gestionar usuarios
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Datos inválidos",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        user_data = serializer.instance

        return Response({
            "user": UsuarioSerializer(user_data, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=partial,
                context={'request': request}
            )

            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "Error inesperado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# MIEMBROS DEL GIMNASIO
# ============================================================

class UsuarioGymViewSet(MultiTenantViewSetMixin, viewsets.ModelViewSet):
    queryset = UsuarioGym.objects.all()
    serializer_class = UsuarioGymSerializer
    permission_classes = [IsAuthenticated, IsRecepcionUser, RequirePasswordChange]  # Admin y recepcion pueden acceder
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'lastname']


class UsuarioGymDayViewSet(MultiTenantViewSetMixin, viewsets.ModelViewSet):
    queryset = UsuarioGymDay.objects.all()
    serializer_class = UsuarioGymDaySerializer
    permission_classes = [IsAuthenticated, IsRecepcionUser, RequirePasswordChange]  # Admin y recepcion pueden acceder
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'lastname']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Datos inválidos para ingreso diario",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)