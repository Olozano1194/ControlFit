"""Renovar (renew) calculation and validation helpers."""

from rest_framework import status
from rest_framework.response import Response
from decimal import Decimal
from datetime import timedelta


def get_membresia_for_renewal(request, asignacion, membresia_id):
    """Get membership for renewal (default to current membership).
    
    Returns tuple (membresia, error_response). If error_response is not None, it's an error.
    """
    from ..models.membership_model import Membresia
    
    if membresia_id:
        try:
            return Membresia.objects.get(
                id=membresia_id,
                gimnasio=request.gimnasio
            ), None
        except Membresia.DoesNotExist:
            return None, Response(
                {'membresia_id': 'La membresía especificada no existe o no pertenece a tu gimnasio'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        return asignacion.membresia, None


def calculate_renewal_price(membresia, multiplier, discount_percent):
    """Calculate price for renewal."""
    price = membresia.price * multiplier * (Decimal('1') - discount_percent / Decimal('100'))
    return price.quantize(Decimal('0.01'))


def calculate_renewal_dates(today, membresia, multiplier):
    """Calculate dateInitial and dateFinal for renewal."""
    dias_totales = int(membresia.duration * multiplier)
    date_initial = today
    date_final = today + timedelta(days=dias_totales)
    return date_initial, date_final, dias_totales


def create_renewal_assignment(request, asignacion, membresia, multiplier, discount_percent, date_initial, price):
    """Create new assignment for renewal."""
    from ..models.membership_model import MembresiaAsignada
    
    return MembresiaAsignada.objects.create(
        gimnasio=request.gimnasio,
        miembro=asignacion.miembro,
        membresia=membresia,
        multiplier=multiplier,
        discount_percent=discount_percent,
        dateInitial=date_initial,
        price=price,
    )