"""
Reservation model — bookings with approval workflow.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True, comment="Assigned room (may be null until confirmed)"
    )
    room_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("room_types.id", ondelete="CASCADE"),
        nullable=False
    )
    guest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("guests.id", ondelete="CASCADE"),
        nullable=False
    )
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False
    )
    total_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    hotel = relationship("Hotel", back_populates="reservations")
    room = relationship("Room", back_populates="reservations")
    room_type = relationship("RoomType", back_populates="reservations")
    guest = relationship("Guest", back_populates="reservations")

    __table_args__ = (
        # Index for fast availability checks
        Index(
            "ix_reservation_availability",
            "hotel_id", "room_type_id", "check_in", "check_out",
        ),
        # Index for pending approvals
        Index("ix_reservation_status", "hotel_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Reservation {self.id} ({self.status.value})>"
