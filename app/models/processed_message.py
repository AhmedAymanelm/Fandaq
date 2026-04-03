"""
ProcessedMessage model — prevents duplicate webhook processing.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True,
        comment="WhatsApp message ID (wamid...)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<ProcessedMessage {self.id}>"
