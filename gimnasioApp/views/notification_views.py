from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from ..serializers import NotificationSerializer
from ..models import Notification
from ..permissions import IsRecepcionUser, RequirePasswordChange
from ..mixins import MultiTenantViewSetMixin
from ..services.notifications import NotificationManager


class NotificationViewSet(MultiTenantViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """API de notificaciones para admin y recepcionistas.

    El listado dispara la generación perezosa e idempotente de notificaciones
    (vencimientos de membresías y eventos del día) y devuelve SOLO las no
    leídas, ordenadas de más reciente a más antigua. Las leídas desaparecen.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsRecepcionUser, RequirePasswordChange]

    def get_queryset(self):
        """Solo notificaciones no leídas del gimnasio del request."""
        queryset = super().get_queryset().filter(is_read=False)
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        # Generación perezosa e idempotente antes de responder
        # Solo generar si hay gimnasio (superadmin no tiene gimnasio)
        if request.gimnasio:
            NotificationManager.generate_for_gimnasio(request.gimnasio)
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='marcar-leida')
    def marcar_leida(self, request, pk=None):
        """Marca una notificación como leída (is_read=True, read_at=ahora)."""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        """Marca todas las notificaciones no leídas del gimnasio como leídas."""
        now = timezone.now()
        # get_queryset ya limita al gimnasio del request y a las no leídas
        marked = self.get_queryset().update(is_read=True, read_at=now)
        return Response({'status': 'ok', 'marked': marked})

    @action(detail=False, methods=['get'], url_path='no-leidas')
    def no_leidas(self, request):
        """Conteo de notificaciones no leídas para el badge del frontend."""
        count = self.get_queryset().count()
        return Response({'count': count})