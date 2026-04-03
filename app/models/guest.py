"""
Guest model — registered guests per hotel.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    whatsapp_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True,
        comment="WhatsApp user ID from webhook payload"
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nationality: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Guest nationality, e.g. سعودي، مصري"
    )
    id_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="Document type: هوية، جواز، إقامة"
    )
    id_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="ID/passport/iqama number"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Special notes about this guest"
    )
    total_stays: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Number of completed stays"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    hotel = relationship("Hotel", back_populates="guests")
    reservations = relationship("Reservation", back_populates="guest", cascade="all, delete-orphan", passive_deletes=True)
    complaints = relationship("Complaint", back_populates="guest", cascade="all, delete-orphan", passive_deletes=True)
    guest_requests = relationship("GuestRequest", back_populates="guest", cascade="all, delete-orphan", passive_deletes=True)
    reviews = relationship("Review", back_populates="guest", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Guest {self.name} ({self.phone})>"

