"""
Date utilities for handling date parsing and calculations.
"""

from datetime import date, datetime, timedelta


def parse_date_string(date_str: str, reference_date: date | None = None) -> date | None:
    """
    Parse various date string formats.

    Supports:
        - YYYY-MM-DD format
        - Relative: 'today', 'tomorrow', 'next week'
    """
    if not date_str:
        return None

    ref = reference_date or date.today()
    date_str_lower = date_str.strip().lower()

    # Relative dates
    if date_str_lower == "today":
        return ref
    elif date_str_lower == "tomorrow":
        return ref + timedelta(days=1)
    elif date_str_lower == "next week":
        return ref + timedelta(weeks=1)
    elif date_str_lower == "yesterday":
        return ref - timedelta(days=1)

    # Standard format
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        pass

    # Try DD/MM/YYYY
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        pass

    return None


def calculate_nights(check_in: date, check_out: date) -> int:
    """Calculate number of nights between check-in and check-out."""
    delta = check_out - check_in
    return max(0, delta.days)


def get_period_dates(period_type: str, reference_date: date | None = None) -> tuple[date, date]:
    """
    Get start and end dates for a period type.

    Args:
        period_type: 'daily', 'weekly', or 'monthly'
        reference_date: Reference date (defaults to today)

    Returns:
        Tuple of (start_date, end_date)
    """
    ref = reference_date or date.today()

    if period_type == "daily":
        return ref, ref
    elif period_type == "weekly":
        start = ref - timedelta(days=ref.weekday())  # Monday
        end = start + timedelta(days=6)               # Sunday
        return start, end
    elif period_type == "monthly":
        start = ref.replace(day=1)
        if ref.month == 12:
            end = ref.replace(year=ref.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = ref.replace(month=ref.month + 1, day=1) - timedelta(days=1)
        return start, end
    else:
        return ref, ref
