"""
Pricing utility — calculate reservation prices.
"""

from datetime import date


def calculate_price(
    check_in: date,
    check_out: date,
    daily_rate: float,
    monthly_rate: float,
) -> float:
    """
    Calculate total price for a stay.

    Uses monthly rate for stays >= 30 days, otherwise daily rate.
    For mixed stays (e.g., 45 days), applies monthly rate for full months
    and daily rate for remaining days.
    """
    total_days = (check_out - check_in).days

    if total_days <= 0:
        return 0.0

    if total_days >= 30:
        # Calculate full months and remaining days
        full_months = total_days // 30
        remaining_days = total_days % 30

        return (full_months * monthly_rate) + (remaining_days * daily_rate)
    else:
        return total_days * daily_rate
