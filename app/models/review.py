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
    sentiment: Mapped[str] = mapped_column(
        String(20), nullable=False, default="neutral", index=True,
        comment="positive, neutral, negative"
    )
    reply_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_approval", index=True,
        comment="auto_sent, pending_approval, approved, sent, rejected"
    )
    final_reply_text: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Final reply text chosen for publishing"
    )
    reply_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reply_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reply_approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    reply_approved_by_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    reply_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reply_sent_channel: Mapped[str | None] = mapped_column(
        String(30), nullable=True,
        comment="auto_policy or manual"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    hotel = relationship("Hotel", back_populates="reviews")
    guest = relationship("Guest", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review {self.rating}★ by Guest {self.guest_id}>"
