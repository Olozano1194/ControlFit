"""Cambiar-plan calculation helpers."""

from rest_framework import status
from rest_framework.response import Response
from decimal import Decimal


def validate_nueva_membresia(nueva_membresia_id, request):
    """Validate and get new membership for plan change."""
    from ..models.membership_model import Membresia
    
    if not nueva_membresia_id:
        return None, Response(
            {'nueva_membresia_id': 'La nueva membresía es obligatoria'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        nueva_membresia = Membresia.objects.get(
            id=nueva_membresia_id,
            gimnasio=request.gimnasio
        )
        return nueva_membresia, None
    except Membresia.DoesNotExist:
        return None, Response(
            {'nueva_membresia_id': 'La membresía especificada no existe o no pertenece a tu gimnasio'},
            status=status.HTTP_400_BAD_REQUEST
        )


def validate_cambiar_plan_multiplier(multiplier_str, nueva_membresia):
    """Validate multiplier for cambiar-plan."""
    try:
        multiplier = Decimal(str(multiplier_str))
        if multiplier < 1:
            return None, Response(
                {'multiplier': 'El multiplicador debe ser al menos 1'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if int(multiplier) > nueva_membresia.max_multiplier:
            if nueva_membresia.max_multiplier <= 1:
                return None, Response(
                    {'multiplier': 'Esa membresía no se puede multiplicar'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return None, Response(
                {'multiplier': f'Esa membresía solo permite hasta {nueva_membresia.max_multiplier} periodos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return multiplier, None
    except (ValueError, TypeError):
        return None, Response(
            {'multiplier': 'El multiplicador debe ser un número válido'},
            status=status.HTTP_400_BAD_REQUEST
        )


def validate_cambiar_plan_discount(discount_str):
    """Validate discount_percent for cambiar-plan."""
    try:
        discount_percent = Decimal(str(discount_str))
        if discount_percent < 0 or discount_percent > 100:
            return None, Response(
                {'discount_percent': 'El descuento debe estar entre 0 y 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return discount_percent, None
    except (ValueError, TypeError):
        return None, Response(
            {'discount_percent': 'El descuento debe ser un número válido'},
            status=status.HTTP_400_BAD_REQUEST
        )


def apply_cambiar_plan(asignacion, nueva_membresia, multiplier, discount_percent, new_date_initial, new_date_final, final_price):
    """Apply plan change via queryset update."""
    from ..models.membership_model import MembresiaAsignada
    MembresiaAsignada.objects.filter(pk=asignacion.pk).update(
        membresia=nueva_membresia,
        dateInitial=new_date_initial,
        dateFinal=new_date_final,
        multiplier=multiplier,
        discount_percent=discount_percent,
        price=final_price
    )