from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from ..serializers import TipoEventoSerializer, EventoCalendarioSerializer
from ..models import TipoEvento, EventoCalendario, Gimnasio
from ..permissions import IsAdminUser, IsRecepcionUser, RequirePasswordChange
from ..mixins import MultiTenantViewSetMixin


class TipoEventoViewSet(MultiTenantViewSetMixin, viewsets.ModelViewSet):
    queryset = TipoEvento.objects.all()
    serializer_class = TipoEventoSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, RequirePasswordChange]


class EventoCalendarioViewSet(MultiTenantViewSetMixin, viewsets.ModelViewSet):
    queryset = EventoCalendario.objects.all()
    serializer_class = EventoCalendarioSerializer
    permission_classes = [IsAuthenticated, IsRecepcionUser, RequirePasswordChange]

    def get_queryset(self):
        qs = super().get_queryset().select_related('tipo')
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start and end:
            qs = qs.filter(fecha_inicio__lte=end, fecha_fin__gte=start)
        return qs.order_by('fecha_inicio')

    def perform_create(self, serializer):
        serializer.save(gimnasio=self.request.gimnasio, created_by=self.request.user)


class PublicCalendarioView(APIView):
    """Endpoint público (sin autenticación) con los eventos de un gimnasio."""
    permission_classes = [AllowAny]

    def get(self, request, gimnasio_id):
        gimnasio = get_object_or_404(Gimnasio, pk=gimnasio_id)
        eventos = EventoCalendario.objects.filter(
            gimnasio=gimnasio
        ).select_related('tipo').order_by('fecha_inicio')
        serializer = EventoCalendarioSerializer(eventos, many=True)
        return Response(serializer.data)