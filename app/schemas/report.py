"""
Report Pydantic schemas.
"""

from datetime import date as date_type
from typing import Optional

from pydantic import BaseModel


class ReportRequest(BaseModel):
    report_type: str  # daily, weekly, monthly
    reference_date: Optional[date_type] = None


class ReportResponse(BaseModel):
    report_type: str
    period_start: str
    period_end: str
    data: dict


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_profit: float
    reservations_count: int
    occupancy_rate: float
    income_by_room_type: dict[str, float]
    expenses_by_category: dict[str, float]
