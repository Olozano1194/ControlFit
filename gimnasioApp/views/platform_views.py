from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal
from ..serializers.platform_serializer import (
    DemoRequestSerializer, PlatformStatsSerializer,
    GimnasioPlatformSerializer, GimnasioPlatformDetailSerializer,
)
from ..models.membership_model import MembresiaAsignada
from ..models.payment_model import PagoMembresia
from ..models.gym_model import Gimnasio
from ..models.demo_model import DemoRequest
from ..models.user_model import Usuario
from ..models.member_model import UsuarioGymDay
from ..permissions import IsSuperAdmin, RequirePasswordChange
from .utils import PlatformPagination
from ..services.onboarding import provision_gym_from_demo, revert_gym_from_demo
from ..services.email import send_welcome_email
import logging


logger = logging.getLogger(__name__)


# ============================================================
# SOLICITUD DE DEMO
# ============================================================

class DemoRequestViewSet(viewsets.ModelViewSet):
    """
    Endpoint para recibir solicitudes de demo desde la landing/login.
    POST público (sin autenticar). GET, PATCH y DELETE solo para superadmins autenticados.
    """
    queryset = DemoRequest.objects.all()
    serializer_class = DemoRequestSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        # PATCH, GET y DELETE requieren superadmin
        return [IsAuthenticated(), IsSuperAdmin()]

    def perform_create(self, serializer):
        # Acá a futuro podés agregar lógica para mandarte un email automático
        serializer.save()

    def _send_welcome_email_safe(self, gym_id: int, admin_id: int, temp_password: str):
        try:
            send_welcome_email(gym_id, admin_id, temp_password)
        except Exception:
            logger.exception("Failed to send welcome email for gym %s, admin %s", gym_id, admin_id)

    def perform_update(self, serializer):
        demo = self.get_object()
        old_estado = demo.estado
        new_estado = serializer.validated_data.get('estado', old_estado)
        
        if old_estado == 'pendiente' and new_estado == 'contactado':
            if demo.gym_creado:
                # Idempotente: ya provisionado, solo actualizar estado
                serializer.save()
                return
            
            try:
                gym, admin, temp_pass = provision_gym_from_demo(demo)
                serializer.save(gym_creado=gym)
                
                # Email sync post-commit (fire-and-forget con logging)
                transaction.on_commit(lambda: self._send_welcome_email_safe(gym.id, admin.id, temp_pass))
                
            except ValidationError as e:
                # Convertir Django ValidationError a DRF ValidationError para 400 response
                from rest_framework.exceptions import ValidationError as DRFValidationError
                raise DRFValidationError(e.messages[0] if e.messages else str(e))
            except Exception as e:
                # Log y re-lanzar como 500
                logger.exception("Error provisioning gym from demo %s", demo.id)
                raise
                
        elif old_estado == 'contactado' and new_estado == 'pendiente':
            # Reverso con cleanup
            revert_gym_from_demo(demo)
            serializer.save(gym_creado=None)
            
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Soft delete: sets estado='cancelada' instead of hard delete."""
        demo = self.get_object()
        if demo.estado == 'cancelada':
            return Response(
                {'detail': 'La solicitud ya está cancelada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        demo.estado = 'cancelada'
        demo.save(update_fields=['estado'])
        serializer = self.get_serializer(demo)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# PLATFORM — SUPERADMIN VIEWS
# ============================================================

class PlatformStatsView(APIView):
    """Estadísticas globales de la plataforma (solo superadmin)."""
    permission_classes = [IsAuthenticated, IsSuperAdmin, RequirePasswordChange]

    def get(self, request):
        today = date.today()
        mes_actual = today.month
        anio_actual = today.year

        # Mes anterior
        if mes_actual == 1:
            prev_month = 12
            prev_year = anio_actual - 1
        else:
            prev_month = mes_actual - 1
            prev_year = anio_actual

        # Total gyms - use all_objects for total, objects already filters active
        total_gimnasios = Gimnasio.all_objects.count()
        gimnasios_activos = Gimnasio.objects.count()

        # Staff total (admin + recepcion + superadmin) - use all_objects for total
        total_usuarios_staff = Usuario.all_objects.count()

        # Demo requests
        demo_pendientes = DemoRequest.objects.filter(estado='pendiente').count()
        demo_contactados = DemoRequest.objects.filter(estado='contactado').count()

        # Ingresos mes global = pagos + diarios (R5)
        pagos_mes = PagoMembresia.objects.filter(
            fecha_pago__month=mes_actual,
            fecha_pago__year=anio_actual
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

        diarios_mes = UsuarioGymDay.objects.filter(
            dateInitial__month=mes_actual,
            dateInitial__year=anio_actual
        ).aggregate(total=Sum('price'))['total'] or Decimal('0')

        ingresos_mes_global = pagos_mes + diarios_mes

        # Miembros activos globales (hoy)
        miembros_activos_global = MembresiaAsignada.objects.filter(
            dateInitial__lte=today,
            dateFinal__gte=today
        ).values('miembro').distinct().count()

        # Retención ponderada: SUM(activos_hoy) / SUM(activos_mes_anterior) * 100
        # Miembros activos mes anterior
        if prev_month == 12:
            prev_month_end = date(prev_year + 1, 1, 1) - timedelta(days=1)
        else:
            prev_month_end = date(prev_year, prev_month + 1, 1) - timedelta(days=1)
        prev_month_start = date(prev_year, prev_month, 1)

        activos_hoy = MembresiaAsignada.objects.filter(
            dateInitial__lte=today,
            dateFinal__gte=today
        ).values('miembro', 'miembro__gimnasio').distinct()

        activos_mes_anterior = MembresiaAsignada.objects.filter(
            dateInitial__lte=prev_month_end,
            dateFinal__gte=prev_month_start
        ).values('miembro', 'miembro__gimnasio').distinct()

        # Agrupar por gimnasio para ponderar
        from collections import defaultdict
        activos_hoy_por_gym = defaultdict(int)
        activos_anterior_por_gym = defaultdict(int)

        for a in activos_hoy:
            activos_hoy_por_gym[a['miembro__gimnasio']] += 1
        for a in activos_mes_anterior:
            activos_anterior_por_gym[a['miembro__gimnasio']] += 1

        total_hoy = sum(activos_hoy_por_gym.values())
        total_anterior = sum(activos_anterior_por_gym.values())

        if total_anterior > 0:
            retencion_promedio = Decimal(str(round((total_hoy / total_anterior) * 100, 1)))
        else:
            retencion_promedio = Decimal('100.0')

        data = {
            'total_gimnasios': total_gimnasios,
            'gimnasios_activos': gimnasios_activos,
            'total_usuarios_staff': total_usuarios_staff,
            'demo_pendientes': demo_pendientes,
            'demo_contactados': demo_contactados,
            'ingresos_mes_global': ingresos_mes_global,
            'miembros_activos_global': miembros_activos_global,
            'retencion_promedio': retencion_promedio,
        }
        serializer = PlatformStatsSerializer(data)
        return Response(serializer.data)


class GimnasioPlatformViewSet(viewsets.ModelViewSet):
    """CRUD de gimnasios para superadmin (sin filtro multi-tenant).
    
    List: solo gimnasios activos (is_active=True)
    Retrieve/Update/Delete: permite acceder a cualquier gym por ID (incluye inactivos para poder reactivarlos)
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin, RequirePasswordChange]
    pagination_class = PlatformPagination
    queryset = Gimnasio.all_objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'address', 'phone']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GimnasioPlatformDetailSerializer
        return GimnasioPlatformSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        
        # LIST: solo gimnasios activos
        if self.action == 'list':
            qs = qs.filter(is_active=True)
            
            today = date.today()
            mes_actual = today.month
            anio_actual = today.year

            qs = qs.annotate(
                usuarios_count=Count(
                    'usuarios',
                    filter=Q(usuarios__is_active=True)
                ),
                miembros_activos_count=Count(
                    'miembros__miembro',
                    filter=Q(
                        miembros__miembro__dateInitial__lte=today,
                        miembros__miembro__dateFinal__gte=today
                    ),
                    distinct=True
                ),
                ingresos_mes=(
                    Sum(
                        'miembros__miembro__pagos__monto',
                        filter=Q(
                            miembros__miembro__pagos__fecha_pago__month=mes_actual,
                            miembros__miembro__pagos__fecha_pago__year=anio_actual
                        )
                    ) or Decimal('0')
                ) + (
                    Sum(
                        'miembros_diarios__price',
                        filter=Q(
                            miembros_diarios__dateInitial__month=mes_actual,
                            miembros_diarios__dateInitial__year=anio_actual
                        )
                    ) or Decimal('0')
                )
            )
        # RETRIEVE/UPDATE/DELETE: todos los gyms (incluye inactivos para poder reactivarlos)
        return qs