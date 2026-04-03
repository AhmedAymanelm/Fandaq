"""
DailyPricing model — tracks daily competitor prices vs our hotel's prices.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DailyPricing(Base):
    __tablename__ = "daily_pricing"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    competitor_hotel_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Name of the competitor hotel"
    )
    date: Mapped[date] = mapped_column(
        Date, nullable=False, default=func.current_date(), 
        comment="Date of the pricing"
    )
    my_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, comment="My hotel's price"
    )
    competitor_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Competitor's price"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Prevent duplicates for the same hotel + competitor + date
    __table_args__ = (
        UniqueConstraint('hotel_id', 'competitor_hotel_name', 'date', name='uq_hotel_competitor_date'),
    )

    hotel = relationship("Hotel", back_populates="daily_prices")
