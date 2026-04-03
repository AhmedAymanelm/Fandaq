"""
Expense Pydantic schemas.
"""

import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    expense_date: date | None = None


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    amount: float
    category: str
    description: str | None
    expense_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    expenses: list[ExpenseResponse]
    total: int
    total_amount: float
