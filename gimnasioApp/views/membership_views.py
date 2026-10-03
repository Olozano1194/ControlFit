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

from .membership_helpers import validate_reason
from .membership_suspender import calculate_suspension_days, apply_suspension
from .membership_cambiar_plan import (
    validate_nueva_membresia,
    validate_cambiar_plan_multiplier,
    validate_cambiar_plan_discount,
    apply_cambiar_plan,
)
from .membership_calculations import (
    calculate_unused_days_credit,
    calculate_new_plan_price,
    calculate_new_dates,
)
from .membership_devolucion import validate_monto, create_refund_payment
from .membership_renovar import (
    get_membresia_for_renewal,
    calculate_renewal_price,
    calculate_renewal_dates,
    create_renewal_assignment,
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
        
        error = validate_reason(request.data.get('reason'), 'suspender')
        if error:
            return error
        
        suspension_days, error = calculate_suspension_days(
            request.data.get('dias'),
            request.data.get('fecha_inicio'),
            request.data.get('fecha_fin')
        )
        if error:
            return error
        
        apply_suspension(asignacion, suspension_days)
        
        # TODO: Audit log - create OperationLog entry when model exists
        
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
        
        error = validate_reason(request.data.get('reason'), 'cambiar el plan')
        if error:
            return error
        
        nueva_membresia, error = validate_nueva_membresia(request.data.get('nueva_membresia_id'), request)
        if error:
            return error
        
        multiplier, error = validate_cambiar_plan_multiplier(request.data.get('multiplier', '1'), nueva_membresia)
        if error:
            return error
        
        discount_percent, error = validate_cambiar_plan_discount(request.data.get('discount_percent', '0'))
        if error:
            return error
        
        original_price = asignacion.price
        original_membresia = asignacion.membresia
        original_multiplier = asignacion.multiplier
        
        unused_days, credit = calculate_unused_days_credit(
            asignacion, today, original_membresia, original_price, original_multiplier
        )
        
        final_price = calculate_new_plan_price(
            nueva_membresia, multiplier, discount_percent, credit
        )
        
        new_date_initial, new_date_final, new_total_days = calculate_new_dates(
            today, nueva_membresia, multiplier
        )
        
        apply_cambiar_plan(
            asignacion, nueva_membresia, multiplier, discount_percent,
            new_date_initial, new_date_final, final_price
        )
        
        asignacion.refresh_from_db()
        
        # TODO: Audit log - create OperationLog entry when model exists
        
        serializer = self.get_serializer(asignacion)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='devolucion')
    def devolucion(self, request, pk=None):
        """
        Registrar una devolución (refund) de una membresía asignada.
        
        Body: {monto, reason}
        - monto: required - monto a devolver (debe ser > 0 y <= total_pagado)
        - reason: required - motivo de la devolución (mín. 10 caracteres)
        
        Lógica:
        1. Crea un registro de pago negativo (PagoMembresia con monto negativo)
        2. Reduce total_pagado
        3. Recalcula saldo_pendiente y estado_pago
        Multi-tenant scoped via gimnasio_field.
        Audit log: TODO - implement when OperationLog model exists.
        """
        asignacion = self.get_object()
        
        error = validate_reason(request.data.get('reason'), 'registrar la devolución')
        if error:
            return error
        
        monto, error = validate_monto(request.data.get('monto'), asignacion.total_pagado)
        if error:
            return error
        
        create_refund_payment(asignacion, monto, request.data.get('reason'))
        
        asignacion.refresh_from_db()
        
        # TODO: Audit log - create OperationLog entry when model exists
        
        serializer = self.get_serializer(asignacion)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='renovar')
    def renovar(self, request, pk=None):
        """
        Renovar una membresía asignada creando una NUEVA asignación.
        
        Body: {membresia_id?, multiplier?, discount_percent?, reason}
        - membresia_id: optional - ID de la membresía para la renovación (default: misma membresía actual)
        - multiplier: optional - multiplicador para el nuevo plan (default: 1)
        - discount_percent: optional - descuento porcentual (default: 0, max: 100)
        - reason: required - motivo de la renovación (mín. 10 caracteres)
        
        Lógica:
        1. Crea una NUEVA MembresiaAsignada (no modifica la existente)
        2. dateInitial = today (o dateFinal de la anterior + 1 día si se quiere continuidad)
        3. dateFinal = dateInitial + (membresia.duration * multiplier)
        4. price = membresia.price * multiplier * (1 - discount/100)
        5. total_pagado = 0, estado_pago = 'pending' (nueva asignación sin pagos)
        Multi-tenant scoped via gimnasio_field.
        Audit log: TODO - implement when OperationLog model exists.
        
        Returns the new assignment.
        """
        asignacion = self.get_object()
        today = self.get_today()
        
        error = validate_reason(request.data.get('reason'), 'renovar la membresía')
        if error:
            return error
        
        membresia, error = get_membresia_for_renewal(request, asignacion, request.data.get('membresia_id'))
        if error:
            return error
        
        multiplier, error = validate_cambiar_plan_multiplier(request.data.get('multiplier', '1'), membresia)
        if error:
            return error
        
        discount_percent, error = validate_cambiar_plan_discount(request.data.get('discount_percent', '0'))
        if error:
            return error
        
        price = calculate_renewal_price(membresia, multiplier, discount_percent)
        date_initial, date_final, dias_totales = calculate_renewal_dates(today, membresia, multiplier)
        
        nueva_asignacion = create_renewal_assignment(
            request, asignacion, membresia, multiplier, discount_percent, date_initial, price
        )
        
        # TODO: Audit log - create OperationLog entry when model exists
        
        serializer = self.get_serializer(nueva_asignacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)