"""add sla tracking to complaints and guest requests

Revision ID: c1b3a92d8f44
Revises: 8e1c4d4a7f3b
Create Date: 2026-04-05 13:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "c1b3a92d8f44"
down_revision = "8e1c4d4a7f3b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("complaints", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("complaints", sa.Column("first_response_by_user_id", sa.UUID(), nullable=True))
    op.add_column("complaints", sa.Column("first_response_by_name", sa.String(length=255), nullable=True))
    op.create_foreign_key(
        "fk_complaints_first_response_by_user_id",
        "complaints",
        "users",
        ["first_response_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_complaints_first_response_by_user_id", "complaints", ["first_response_by_user_id"], unique=False)

    op.add_column("guest_requests", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("guest_requests", sa.Column("first_response_by_user_id", sa.UUID(), nullable=True))
    op.add_column("guest_requests", sa.Column("first_response_by_name", sa.String(length=255), nullable=True))
    op.add_column("guest_requests", sa.Column("completed_by_user_id", sa.UUID(), nullable=True))
    op.add_column("guest_requests", sa.Column("completed_by_name", sa.String(length=255), nullable=True))

    op.create_foreign_key(
        "fk_guest_requests_first_response_by_user_id",
        "guest_requests",
        "users",
        ["first_response_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_guest_requests_completed_by_user_id",
        "guest_requests",
        "users",
        ["completed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_guest_requests_first_response_by_user_id", "guest_requests", ["first_response_by_user_id"], unique=False)
    op.create_index("ix_guest_requests_completed_by_user_id", "guest_requests", ["completed_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_guest_requests_completed_by_user_id", table_name="guest_requests")
    op.drop_index("ix_guest_requests_first_response_by_user_id", table_name="guest_requests")
    op.drop_constraint("fk_guest_requests_completed_by_user_id", "guest_requests", type_="foreignkey")
    op.drop_constraint("fk_guest_requests_first_response_by_user_id", "guest_requests", type_="foreignkey")
    op.drop_column("guest_requests", "completed_by_name")
    op.drop_column("guest_requests", "completed_by_user_id")
    op.drop_column("guest_requests", "first_response_by_name")
    op.drop_column("guest_requests", "first_response_by_user_id")
    op.drop_column("guest_requests", "acknowledged_at")

    op.drop_index("ix_complaints_first_response_by_user_id", table_name="complaints")
    op.drop_constraint("fk_complaints_first_response_by_user_id", "complaints", type_="foreignkey")
    op.drop_column("complaints", "first_response_by_name")
    op.drop_column("complaints", "first_response_by_user_id")
    op.drop_column("complaints", "acknowledged_at")
