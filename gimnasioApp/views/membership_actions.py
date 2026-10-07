"""Action implementations for MembresiaAsignadaViewSet.

Each function receives (request, viewset, asignacion) and returns
(Response, status_code) or raises validation errors.
"""

from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from datetime import date
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
from .membership_audit import log_operation


def suspender_action(request, viewset, asignacion):
    """Handle suspender action logic.
    
    Body: {fecha_inicio?, fecha_fin?, dias?, reason}
    - reason: required
    - fecha_inicio: start date of suspension (optional, defaults to today)
    - fecha_fin: end date of suspension (optional)
    - dias: number of days to suspend (optional, alternative to fecha_fin)
    """
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

    reason = request.data.get('reason')

    with transaction.atomic():
        original_date_final = asignacion.dateFinal
        apply_suspension(asignacion, suspension_days)

        log_operation(
            request=request,
            asignacion=asignacion,
            operation_type='suspender',
            reason=reason,
            details={
                'dias': suspension_days,
                'original_date_final': original_date_final.isoformat(),
                'new_date_final': asignacion.dateFinal.isoformat(),
            }
        )

    serializer = viewset.get_serializer(asignacion)
    return Response(serializer.data, status=status.HTTP_200_OK)


def cambiar_plan_action(request, viewset, asignacion):
    """Handle cambiar-plan action logic.
    
    Body: {nueva_membresia_id, reason, multiplier?, discount_percent?}
    - nueva_membresia_id: required - ID de la nueva membresía
    - reason: required - motivo del cambio (mín. 10 caracteres)
    - multiplier: optional - multiplicador para el nuevo plan (default: 1)
    - discount_percent: optional - descuento porcentual (default: 0, max: 100)
    """
    today = viewset.get_today()

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

    reason = request.data.get('reason')

    with transaction.atomic():
        apply_cambiar_plan(
            asignacion, nueva_membresia, multiplier, discount_percent,
            new_date_initial, new_date_final, final_price
        )

        asignacion.refresh_from_db()

        log_operation(
            request=request,
            asignacion=asignacion,
            operation_type='cambiar_plan',
            reason=reason,
            details={
                'membresia_anterior': original_membresia.id,
                'membresia_nueva': nueva_membresia.id,
                'credit': str(credit),
                'final_price': str(final_price),
            }
        )

    serializer = viewset.get_serializer(asignacion)
    return Response(serializer.data, status=status.HTTP_200_OK)


def devolucion_action(request, viewset, asignacion):
    """Handle devolucion (refund) action logic.
    
    Body: {monto, reason}
    - monto: required - monto a devolver (debe ser > 0 y <= total_pagado)
    - reason: required - motivo de la devolución (mín. 10 caracteres)
    """
    error = validate_reason(request.data.get('reason'), 'registrar la devolución')
    if error:
        return error

    monto, error = validate_monto(request.data.get('monto'), asignacion.total_pagado)
    if error:
        return error

    reason = request.data.get('reason')

    total_pagado_before = asignacion.total_pagado

    with transaction.atomic():
        create_refund_payment(asignacion, monto, reason)

        asignacion.refresh_from_db()

        log_operation(
            request=request,
            asignacion=asignacion,
            operation_type='devolucion',
            reason=reason,
            details={
                'monto': str(monto),
                'total_pagado_before': str(total_pagado_before),
            }
        )

    serializer = viewset.get_serializer(asignacion)
    return Response(serializer.data, status=status.HTTP_200_OK)


def renovar_action(request, viewset, asignacion):
    """Handle renovar action logic.
    
    Body: {membresia_id?, multiplier?, discount_percent?, reason}
    - membresia_id: optional - ID de la membresía para la renovación (default: misma membresía actual)
    - multiplier: optional - multiplicador para el nuevo plan (default: 1)
    - discount_percent: optional - descuento porcentual (default: 0, max: 100)
    - reason: required - motivo de la renovación (mín. 10 caracteres)
    """
    today = viewset.get_today()

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

    reason = request.data.get('reason')

    with transaction.atomic():
        nueva_asignacion = create_renewal_assignment(
            request, asignacion, membresia, multiplier, discount_percent, date_initial, price
        )

        log_operation(
            request=request,
            asignacion=asignacion,
            operation_type='renovar',
            reason=reason,
            details={
                'nueva_asignacion_id': nueva_asignacion.id,
                'membresia': membresia.id,
                'price': str(price),
            }
        )

    serializer = viewset.get_serializer(nueva_asignacion)
    return Response(serializer.data, status=status.HTTP_201_CREATED)