"""
Expense service — track expenses per hotel.
"""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense


class ExpenseService:

    @staticmethod
    async def add_expense(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        amount: float,
        category: str,
        description: str | None = None,
        expense_date: date | None = None,
    ) -> Expense:
        """Add a new expense record."""
        expense = Expense(
            hotel_id=hotel_id,
            amount=amount,
            category=category.strip().lower(),
            description=description,
            expense_date=expense_date or date.today(),
        )
        db.add(expense)
        await db.flush()
        return expense

    @staticmethod
    async def list_expenses(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        category: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """List expenses with optional filters."""
        stmt = select(Expense).where(Expense.hotel_id == hotel_id)
        count_stmt = select(func.count(Expense.id)).where(Expense.hotel_id == hotel_id)
        sum_stmt = select(func.sum(Expense.amount)).where(Expense.hotel_id == hotel_id)

        if start_date:
            stmt = stmt.where(Expense.expense_date >= start_date)
            count_stmt = count_stmt.where(Expense.expense_date >= start_date)
            sum_stmt = sum_stmt.where(Expense.expense_date >= start_date)
        if end_date:
            stmt = stmt.where(Expense.expense_date <= end_date)
            count_stmt = count_stmt.where(Expense.expense_date <= end_date)
            sum_stmt = sum_stmt.where(Expense.expense_date <= end_date)
        if category:
            stmt = stmt.where(Expense.category == category.strip().lower())
            count_stmt = count_stmt.where(Expense.category == category.strip().lower())
            sum_stmt = sum_stmt.where(Expense.category == category.strip().lower())

        stmt = stmt.order_by(Expense.expense_date.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        expenses = result.scalars().all()

        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        sum_result = await db.execute(sum_stmt)
        total_amount = float(sum_result.scalar() or 0)

        return {
            "expenses": expenses,
            "total": total,
            "total_amount": total_amount,
        }

    @staticmethod
    async def get_expenses_by_category(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict[str, float]:
        """Get expense totals grouped by category."""
        stmt = (
            select(Expense.category, func.sum(Expense.amount))
            .where(
                Expense.hotel_id == hotel_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(Expense.category)
        )
        result = await db.execute(stmt)
        return {row[0]: float(row[1]) for row in result.all()}
