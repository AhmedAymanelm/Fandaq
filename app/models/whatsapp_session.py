"""
WhatsAppSession model — conversation context tracking.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    whatsapp_user_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="Sender phone number / WhatsApp ID"
    )
    context: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=dict,
        comment="Conversation state for multi-turn flows"
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    hotel = relationship("Hotel", back_populates="whatsapp_sessions")

    def __repr__(self) -> str:
        return f"<WhatsAppSession {self.whatsapp_user_id} @ Hotel {self.hotel_id}>"
