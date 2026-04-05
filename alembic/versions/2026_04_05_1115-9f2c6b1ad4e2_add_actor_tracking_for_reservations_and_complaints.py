"""add_actor_tracking_for_reservations_and_complaints

Revision ID: 9f2c6b1ad4e2
Revises: 5c9f1f5b83e1
Create Date: 2026-04-05 11:15:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f2c6b1ad4e2'
down_revision: Union[str, None] = '5c9f1f5b83e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reservations', sa.Column('approved_by_user_id', sa.UUID(), nullable=True, comment='User who approved this reservation'))
    op.add_column('reservations', sa.Column('approved_by_name', sa.String(length=255), nullable=True, comment='Snapshot name of approver'))
    op.add_column('reservations', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_reservations_approved_by_user_id'), 'reservations', ['approved_by_user_id'], unique=False)
    op.create_foreign_key('fk_reservations_approved_by_user_id_users', 'reservations', 'users', ['approved_by_user_id'], ['id'], ondelete='SET NULL')

    op.add_column('complaints', sa.Column('resolved_by_user_id', sa.UUID(), nullable=True, comment='User who resolved this complaint'))
    op.add_column('complaints', sa.Column('resolved_by_name', sa.String(length=255), nullable=True, comment='Snapshot name of resolver'))
    op.create_index(op.f('ix_complaints_resolved_by_user_id'), 'complaints', ['resolved_by_user_id'], unique=False)
    op.create_foreign_key('fk_complaints_resolved_by_user_id_users', 'complaints', 'users', ['resolved_by_user_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_complaints_resolved_by_user_id_users', 'complaints', type_='foreignkey')
    op.drop_index(op.f('ix_complaints_resolved_by_user_id'), table_name='complaints')
    op.drop_column('complaints', 'resolved_by_name')
    op.drop_column('complaints', 'resolved_by_user_id')

    op.drop_constraint('fk_reservations_approved_by_user_id_users', 'reservations', type_='foreignkey')
    op.drop_index(op.f('ix_reservations_approved_by_user_id'), table_name='reservations')
    op.drop_column('reservations', 'approved_at')
    op.drop_column('reservations', 'approved_by_name')
    op.drop_column('reservations', 'approved_by_user_id')
