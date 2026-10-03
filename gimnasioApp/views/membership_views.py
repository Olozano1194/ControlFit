from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from ..serializers.membership_serializer import MembresiasSerializer, MembresiaAsignadaSerializer
from ..models.membership_model import Membresia, MembresiaAsignada
from ..permissions import IsRecepcionUser, RequirePasswordChange
from ..mixins import MultiTenantViewSetMixin
from datetime import date, timedelta
from decimal import Decimal


class MembresiaViewSet(MultiTenantViewSetMixin, viewsets.ModelViewSet):
    queryset = Membresia.objects.all()
    serializer_class = MembresiasSerializer
    permission_classes = [IsAuthenticated, IsRecepcionUser, RequirePasswordChange]


class MembresiaAsignadaViewSet(MultiTenantViewSetMixin, viewsets.ModelViewSet):
    queryset = MembresiaAsignada.objects.all()
    serializer_class = MembresiaAsignadaSerializer
    permission_classes = [IsAuthenticated, IsRecepcionUser, RequirePasswordChange]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['miembro__name', 'miembro__lastname']
    gimnasio_field = 'miembro__gimnasio'

    def get_queryset(self):
        """Filtrar membresías asignadas por gimnasio del usuario actual."""
        queryset = super().get_queryset()

        # Filtro adicional por miembro si se pasa
        miembro_id = self.request.query_params.get('miembro')
        if miembro_id:
            queryset = queryset.filter(miembro_id=miembro_id)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'], url_path='suspender')
    def suspender(self, request, pk=None):
        """
        Suspender una membresía asignada.
        
        Body: {fecha_inicio?, fecha_fin?, dias?, reason}
        - reason: required
        - fecha_inicio: start date of suspension (optional, defaults to today)
        - fecha_fin: end date of suspension (optional)
        - dias: number of days to suspend (optional, alternative to fecha_fin)
        
        Updates dateFinal by extending it with the suspension days.
        Multi-tenant scoped via gimnasio_field.
        Audit log: TODO - implement when OperationLog model exists.
        """
        asignacion = self.get_object()
        
        # Validate required reason
        reason = request.data.get('reason')
        if not reason or not reason.strip():
            return Response(
                {'reason': 'El motivo es obligatorio para suspender la membresía'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse suspension parameters
        fecha_inicio_str = request.data.get('fecha_inicio')
        fecha_fin_str = request.data.get('fecha_fin')
        dias_str = request.data.get('dias')
        
        # Calculate suspension days
        suspension_days = 0
        
        if dias_str is not None:
            try:
                suspension_days = int(dias_str)
                if suspension_days <= 0:
                    return Response(
                        {'dias': 'Los días de suspensión deben ser un número positivo'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'dias': 'Los días deben ser un número entero válido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif fecha_inicio_str and fecha_fin_str:
            try:
                fecha_inicio = date.fromisoformat(fecha_inicio_str)
                fecha_fin = date.fromisoformat(fecha_fin_str)
                if fecha_fin <= fecha_inicio:
                    return Response(
                        {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                suspension_days = (fecha_fin - fecha_inicio).days
            except (ValueError, TypeError):
                return Response(
                    {'fecha': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'detail': 'Debe proporcionar "dias" o ambas "fecha_inicio" y "fecha_fin"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extend dateFinal by suspension days
        # The suspension effectively pauses the membership, so we push the end date forward
        original_date_final = asignacion.dateFinal
        asignacion.dateFinal = original_date_final + timedelta(days=suspension_days)
        asignacion.save(update_fields=['dateFinal'])
        
        # TODO: Audit log - create OperationLog entry when model exists
        # OperationLog.objects.create(
        #     gimnasio=request.gimnasio,
        #     usuario=request.user,
        #     operacion='suspender',
        #     asignacion=asignacion,
        #     reason=reason,
        #     campos_afectados={'dateFinal': {'antes': original_date_final.isoformat(), 'despues': asignacion.dateFinal.isoformat()}},
        #     dias_suspension=suspension_days,
        # )
        
        # Return updated assignment
        serializer = self.get_serializer(asignacion)
        return Response(serializer.data, status=status.HTTP_200_OK)