"""
Expenses API — track expenses per hotel.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role_for_hotel
from app.database import get_db
from app.models.user import UserRole
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseListResponse
from app.services.expense import ExpenseService

router = APIRouter(dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN))])


@router.post(
    "/hotels/{hotel_id}/expenses",
    response_model=ExpenseResponse,
    status_code=201,
)
async def add_expense(
    hotel_id: uuid.UUID,
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a new expense."""
    expense = await ExpenseService.add_expense(
        db, hotel_id,
        amount=data.amount,
        category=data.category,
        description=data.description,
        expense_date=data.expense_date,
    )
    return expense


@router.get("/hotels/{hotel_id}/expenses", response_model=ExpenseListResponse)
async def list_expenses(
    hotel_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    skip: int = 0,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List expenses with optional date and category filters."""
    result = await ExpenseService.list_expenses(
        db, hotel_id,
        start_date=start_date,
        end_date=end_date,
        category=category,
        skip=skip,
        limit=limit,
    )
    return result
