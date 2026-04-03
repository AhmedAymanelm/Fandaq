"""
AuditLog model — tracks important actions like owner approvals and rejections.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    actor_phone: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="The WhatsApp number of the user performing the action"
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="e.g., APPROVE_RESERVATION, REJECT_RESERVATION"
    )
    target_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True,
        comment="The ID of the impacted resource (reservation_id, etc.)"
    )
    details: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Extra JSON or text details about the action"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    hotel = relationship("Hotel")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.actor_phone} @ Hotel {self.hotel_id}>"
