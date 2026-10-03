"""Validation helpers for membership operations."""

from rest_framework import status
from rest_framework.response import Response
from decimal import Decimal, ROUND_HALF_UP


def validate_reason(reason: str | None, operation: str) -> Response | None:
    """Validate reason field is present and has minimum length."""
    if not reason or not reason.strip():
        return Response(
            {'reason': f'El motivo es obligatorio para {operation} la membresía'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(reason.strip()) < 10:
        return Response(
            {'reason': 'El motivo debe tener al menos 10 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return None


def validate_positive_integer(value: str | None, field_name: str, min_value: int = 1) -> tuple[int | None, Response | None]:
    """Validate and parse a positive integer field."""
    if value is None:
        return None, Response(
            {field_name: f'El campo {field_name} es obligatorio'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        parsed = int(value)
        if parsed < min_value:
            return None, Response(
                {field_name: f'{field_name} debe ser al menos {min_value}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return parsed, None
    except (ValueError, TypeError):
        return None, Response(
            {field_name: f'{field_name} debe ser un número entero válido'},
            status=status.HTTP_400_BAD_REQUEST
        )


def validate_decimal_range(
    value: str | None, 
    field_name: str, 
    min_val: Decimal | None = None, 
    max_val: Decimal | None = None,
    default: Decimal | None = None
) -> tuple[Decimal | None, Response | None]:
    """Validate and parse a decimal field within range."""
    if value is None:
        if default is not None:
            return default, None
        return None, Response(
            {field_name: f'El campo {field_name} es obligatorio'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        parsed = Decimal(str(value))
        if min_val is not None and parsed < min_val:
            return None, Response(
                {field_name: f'{field_name} debe ser al menos {min_val}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if max_val is not None and parsed > max_val:
            return None, Response(
                {field_name: f'{field_name} debe ser como máximo {max_val}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return parsed, None
    except (ValueError, TypeError):
        return None, Response(
            {field_name: f'{field_name} debe ser un número válido'},
            status=status.HTTP_400_BAD_REQUEST
        )


def validate_suspension_params(
    dias: str | None, 
    fecha_inicio: str | None, 
    fecha_fin: str | None
) -> tuple[int | None, Response | None]:
    """Validate suspension parameters and calculate days."""
    if dias is not None:
        return validate_positive_integer(dias, 'dias')
    
    if fecha_inicio and fecha_fin:
        from datetime import date
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


def round_decimal(value: Decimal) -> Decimal:
    """Round decimal to 2 places with HALF_UP rounding."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)