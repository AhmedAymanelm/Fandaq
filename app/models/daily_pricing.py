"""
DailyPricing model — tracks daily competitor prices vs our hotel's prices.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
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
    room_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_types.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Room type this pricing row belongs to"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    hotel = relationship("Hotel", back_populates="daily_prices")
    room_type = relationship("RoomType")
