"""fix_daily_pricing_uniqueness_with_nullable_room_type

Revision ID: 5c9f1f5b83e1
Revises: 696691a49055
Create Date: 2026-04-05 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c9f1f5b83e1'
down_revision: Union[str, None] = '696691a49055'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop nullable unique constraint that does not protect NULL room_type_id rows.
    op.drop_constraint('uq_hotel_competitor_room_date', 'daily_pricing', type_='unique')

    # Enforce uniqueness for rows without room_type_id.
    op.create_index(
        'uq_daily_pricing_hotel_competitor_date_null_room_type',
        'daily_pricing',
        ['hotel_id', 'competitor_hotel_name', 'date'],
        unique=True,
        postgresql_where=sa.text('room_type_id IS NULL'),
    )

    # Enforce uniqueness for rows with room_type_id.
    op.create_index(
        'uq_daily_pricing_hotel_competitor_room_date_not_null',
        'daily_pricing',
        ['hotel_id', 'competitor_hotel_name', 'room_type_id', 'date'],
        unique=True,
        postgresql_where=sa.text('room_type_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_daily_pricing_hotel_competitor_room_date_not_null', table_name='daily_pricing')
    op.drop_index('uq_daily_pricing_hotel_competitor_date_null_room_type', table_name='daily_pricing')

    op.create_unique_constraint(
        'uq_hotel_competitor_room_date',
        'daily_pricing',
        ['hotel_id', 'competitor_hotel_name', 'room_type_id', 'date'],
    )
