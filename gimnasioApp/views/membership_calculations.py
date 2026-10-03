"""Calculation helpers for membership operations."""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta


def calculate_unused_days_credit(
    asignacion,
    today: date,
    original_membresia,
    original_price: Decimal,
    original_multiplier
) -> tuple[int, Decimal]:
    """
    Calculate unused days and credit amount from current plan.
    
    Returns:
        (unused_days, credit_amount)
    """
    # Current plan's total days = duration * current_multiplier
    current_total_days = int(original_membresia.duration * original_multiplier)
    current_daily_rate = original_price / Decimal(str(current_total_days)) if current_total_days > 0 else Decimal('0')
    
    # Unused days = (dateFinal - today).days
    unused_days = (asignacion.dateFinal - today).days
    if unused_days < 0:
        unused_days = 0
    
    credit = current_daily_rate * Decimal(str(unused_days))
    credit = round_decimal(credit)
    
    return unused_days, credit


def calculate_new_plan_price(
    nueva_membresia,
    multiplier: Decimal,
    discount_percent: Decimal,
    credit: Decimal
) -> Decimal:
    """
    Calculate new plan price with multiplier, discount, and credit applied.
    
    Returns:
        final_price (rounded to 2 decimals, minimum 0)
    """
    new_plan_base_price = nueva_membresia.price * multiplier
    discount_factor = Decimal('1') - discount_percent / Decimal('100')
    new_plan_total = round_decimal(new_plan_base_price * discount_factor)
    
    final_price = round_decimal(new_plan_total - credit)
    if final_price < 0:
        final_price = Decimal('0')
    
    return final_price


def calculate_new_dates(
    today: date,
    nueva_membresia,
    multiplier: Decimal
) -> tuple[date, date, int]:
    """
    Calculate new dateInitial, dateFinal, and total days.
    
    Returns:
        (dateInitial, dateFinal, total_days)
    """
    new_total_days = int(nueva_membresia.duration * multiplier)
    new_date_initial = today
    new_date_final = today + timedelta(days=new_total_days)
    
    return new_date_initial, new_date_final, new_total_days


def round_decimal(value: Decimal) -> Decimal:
    """Round decimal to 2 places with HALF_UP rounding."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)