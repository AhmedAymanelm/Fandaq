"""
WhatsApp Session service — manages multi-turn conversation context.
"""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.whatsapp_session import WhatsAppSession


class WhatsAppSessionService:
    @staticmethod
    async def get_or_create_session(
        db: AsyncSession, hotel_id: uuid.UUID, whatsapp_user_id: str
    ) -> WhatsAppSession:
        """Get an existing session or create a new one."""
        stmt = select(WhatsAppSession).where(
            WhatsAppSession.hotel_id == hotel_id,
            WhatsAppSession.whatsapp_user_id == whatsapp_user_id,
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            session = WhatsAppSession(
                hotel_id=hotel_id,
                whatsapp_user_id=whatsapp_user_id,
                context={"history": []},
            )
            db.add(session)
            await db.flush()

        return session

    @staticmethod
    async def append_to_history(
        db: AsyncSession, session_id: uuid.UUID, role: str, content: str, max_turns: int = 10
    ):
        """Append a message to the session history, keeping only the last `max_turns` messages."""
        stmt = select(WhatsAppSession).where(WhatsAppSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            history = session.context.get("history", []) if session.context else []
            history.append({"role": role, "content": content})
            
            # Keep only the last `max_turns` messages to prevent prompt getting too large
            if len(history) > max_turns:
                history = history[-max_turns:]
            
            # Update contexts and last_message_at
            context = session.context or {}
            context["history"] = history
            
            await db.execute(
                update(WhatsAppSession)
                .where(WhatsAppSession.id == session_id)
                .values(context=context, last_message_at=datetime.utcnow())
            )
            await db.flush()
