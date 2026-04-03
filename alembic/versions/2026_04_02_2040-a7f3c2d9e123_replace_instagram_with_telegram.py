"""Replace instagram_page_id with telegram_owner_chat_id

Revision ID: a7f3c2d9e123
Revises: d1523a701222
Create Date: 2026-04-02 20:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7f3c2d9e123'
down_revision: Union[str, None] = 'd1523a701222'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop Instagram column and index
    op.drop_index(op.f('ix_hotels_instagram_page_id'), table_name='hotels')
    op.drop_column('hotels', 'instagram_page_id')

    # Add Telegram column and index
    op.add_column('hotels', sa.Column(
        'telegram_owner_chat_id',
        sa.String(length=100),
        nullable=True,
        comment='Telegram chat ID of the hotel owner for notifications'
    ))
    op.create_index(
        op.f('ix_hotels_telegram_owner_chat_id'),
        'hotels',
        ['telegram_owner_chat_id'],
        unique=False
    )


def downgrade() -> None:
    # Drop Telegram column and index
    op.drop_index(op.f('ix_hotels_telegram_owner_chat_id'), table_name='hotels')
    op.drop_column('hotels', 'telegram_owner_chat_id')

    # Restore Instagram column and index
    op.add_column('hotels', sa.Column(
        'instagram_page_id',
        sa.String(length=100),
        nullable=True,
        comment='Instagram Page ID linked to this hotel for DM bookings'
    ))
    op.create_index(
        op.f('ix_hotels_instagram_page_id'),
        'hotels',
        ['instagram_page_id'],
        unique=False
    )
