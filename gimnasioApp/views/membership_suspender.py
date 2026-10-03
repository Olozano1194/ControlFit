"""Suspender calculation and validation helpers."""

from rest_framework import status
from rest_framework.response import Response
from datetime import date, timedelta


def calculate_suspension_days(dias, fecha_inicio, fecha_fin):
    """Calculate suspension days from parameters."""
    if dias is not None:
        try:
            suspension_days = int(dias)
            if suspension_days <= 0:
                return None, Response(
                    {'dias': 'Los días de suspensión deben ser un número positivo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return suspension_days, None
        except (ValueError, TypeError):
            return None, Response(
                {'dias': 'Los días deben ser un número entero válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if fecha_inicio and fecha_fin:
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            if ff <= fi:
                return None, Response(
                    {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return (ff - fi).days, None
        except (ValueError, TypeError):
            return None, Response(
                {'fecha': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return None, Response(
        {'detail': 'Debe proporcionar "dias" o ambas "fecha_inicio" y "fecha_fin"'},
        status=status.HTTP_400_BAD_REQUEST
    )


def apply_suspension(asignacion, suspension_days):
    """Apply suspension by extending dateFinal."""
    original_date_final = asignacion.dateFinal
    asignacion.dateFinal = original_date_final + timedelta(days=suspension_days)
    asignacion.save(update_fields=['dateFinal'])
    return original_date_final