"""
Review model — guest reviews/ratings per hotel.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    guest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("guests.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    reservation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reservations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional link to the specific reservation being reviewed"
    )
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Rating 1-5 stars"
    )
    comment: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Guest review text"
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general",
        comment="Category: cleanliness, service, maintenance, general"
    )
    ai_reply_suggestion: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="AI generated suggested reply to the guest"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    hotel = relationship("Hotel", back_populates="reviews")
    guest = relationship("Guest", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review {self.rating}★ by Guest {self.guest_id}>"
