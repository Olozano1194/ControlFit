"""Devolucion (refund) calculation and validation helpers."""

from rest_framework import status
from rest_framework.response import Response
from decimal import Decimal


def validate_monto(monto, total_pagado):
    """Validate monto for devolucion."""
    if monto is None:
        return None, Response(
            {'monto': 'El monto es obligatorio'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        monto = Decimal(str(monto))
    except (ValueError, TypeError):
        return None, Response(
            {'monto': 'El monto debe ser un número válido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if monto <= 0:
        return None, Response(
            {'monto': 'El monto debe ser mayor a 0'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check monto doesn't exceed total_pagado (what was actually paid)
    # This allows refunds even when fully paid (saldo_pendiente = 0)
    if monto > total_pagado:
        return None, Response(
            {'monto': f'El monto no puede exceder el total pagado ({total_pagado})'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return monto, None


def create_refund_payment(asignacion, monto, reason):
    """Create negative payment record for refund."""
    from ..models.payment_model import PagoMembresia
    
    return PagoMembresia.objects.create(
        membresia_asignada=asignacion,
        monto=-monto,
        metodo_pago='efectivo',  # Refunds recorded as cash by default
        nota=f'Devolución: {reason.strip()}'
    )