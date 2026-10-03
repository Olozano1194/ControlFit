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

from .membership_helpers import (
    validate_reason,
    validate_suspension_params,
    validate_positive_integer,
    validate_decimal_range,
)
from .membership_calculations import (
    calculate_unused_days_credit,
    calculate_new_plan_price,
    calculate_new_dates,
)


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

    def get_today(self):
        """Get current date. Override in tests for deterministic behavior."""
        return date.today()

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
        error = validate_reason(request.data.get('reason'), 'suspender')
        if error:
            return error
        
        # Parse and validate suspension parameters
        suspension_days, error = validate_suspension_params(
            request.data.get('dias'),
            request.data.get('fecha_inicio'),
            request.data.get('fecha_fin')
        )
        if error:
            return error
        
        # Extend dateFinal by suspension days
        original_date_final = asignacion.dateFinal
        asignacion.dateFinal = original_date_final + timedelta(days=suspension_days)
        asignacion.save(update_fields=['dateFinal'])
        
        # TODO: Audit log - create OperationLog entry when model exists
        
        # Return updated assignment
        serializer = self.get_serializer(asignacion)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cambiar-plan')
    def cambiar_plan(self, request, pk=None):
        """
        Cambiar el plan de una membresía asignada con crédito por días no usados.
        
        Body: {nueva_membresia_id, reason, multiplier?, discount_percent?}
        - nueva_membresia_id: required - ID de la nueva membresía
        - reason: required - motivo del cambio (mín. 10 caracteres)
        - multiplier: optional - multiplicador para el nuevo plan (default: 1)
        - discount_percent: optional - descuento porcentual (default: 0, max: 100)
        
        Lógica de crédito:
        1. Calcular días no usados del plan actual: (dateFinal - today).days
        2. Calcular tasa diaria del plan actual: price / (duration * multiplier)
        3. Crédito = días_no_usados * tasa_diaria
        4. Precio nuevo plan = (nueva_membresia.price * multiplier * (1 - discount/100)) - crédito
        5. dateInitial = today
        6. dateFinal = today + (nueva_membresia.duration * multiplier)
        
        Preserva snapshots contables: price (original), total_pagado, saldo_pendiente, estado_pago
        Multi-tenant scoped via gimnasio_field.
        Audit log: TODO - implement when OperationLog model exists.
        """
        asignacion = self.get_object()
        today = self.get_today()
        
        # Validate required fields
        error = validate_reason(request.data.get('reason'), 'cambiar el plan')
        if error:
            return error
        
        # Validate nueva_membresia_id
        nueva_membresia_id = request.data.get('nueva_membresia_id')
        if not nueva_membresia_id:
            return Response(
                {'nueva_membresia_id': 'La nueva membresía es obligatoria'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get new membership (must be in same gimnasio)
        try:
            nueva_membresia = Membresia.objects.get(
                id=nueva_membresia_id,
                gimnasio=request.gimnasio
            )
        except Membresia.DoesNotExist:
            return Response(
                {'nueva_membresia_id': 'La membresía especificada no existe o no pertenece a tu gimnasio'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse and validate multiplier
        multiplier, error = validate_decimal_range(
            request.data.get('multiplier', '1'),
            'multiplier',
            min_val=Decimal('1'),
            default=Decimal('1')
        )
        if error:
            return error
        
        # Validate against new plan's max_multiplier
        if int(multiplier) > nueva_membresia.max_multiplier:
            if nueva_membresia.max_multiplier <= 1:
                return Response(
                    {'multiplier': 'Esa membresía no se puede multiplicar'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'multiplier': f'Esa membresía solo permite hasta {nueva_membresia.max_multiplier} periodos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse and validate discount_percent
        discount_percent, error = validate_decimal_range(
            request.data.get('discount_percent', '0'),
            'discount_percent',
            min_val=Decimal('0'),
            max_val=Decimal('100'),
            default=Decimal('0')
        )
        if error:
            return error
        
        # Store original values for snapshot preservation
        original_price = asignacion.price
        original_membresia = asignacion.membresia
        original_multiplier = asignacion.multiplier
        
        # Calculate credit from unused days
        unused_days, credit = calculate_unused_days_credit(
            asignacion, today, original_membresia, original_price, original_multiplier
        )
        
        # Calculate new plan price with credit
        final_price = calculate_new_plan_price(
            nueva_membresia, multiplier, discount_percent, credit
        )
        
        # Calculate new dates
        new_date_initial, new_date_final, new_total_days = calculate_new_dates(
            today, nueva_membresia, multiplier
        )
        
        # Update assignment using queryset update to bypass model.save() recalculation
        MembresiaAsignada.objects.filter(pk=asignacion.pk).update(
            membresia=nueva_membresia,
            dateInitial=new_date_initial,
            dateFinal=new_date_final,
            multiplier=multiplier,
            discount_percent=discount_percent,
            price=final_price
        )
        
        # Refresh from DB to get computed properties
        asignacion.refresh_from_db()
        
        # TODO: Audit log - create OperationLog entry when model exists
        
        # Return updated assignment
        serializer = self.get_serializer(asignacion)
        return Response(serializer.data, status=status.HTTP_200_OK)