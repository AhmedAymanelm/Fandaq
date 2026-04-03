"""
RoomType model — defines categories of rooms per hotel.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RoomType(Base):
    __tablename__ = "room_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="e.g. one-bedroom, two-bedroom, three-bedroom"
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    daily_rate: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Price per day"
    )
    monthly_rate: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Price per month"
    )
    total_units: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Total rooms of this type"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    hotel = relationship("Hotel", back_populates="room_types")
    rooms = relationship("Room", back_populates="room_type", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="room_type")

    def __repr__(self) -> str:
        return f"<RoomType {self.name} @ Hotel {self.hotel_id}>"
