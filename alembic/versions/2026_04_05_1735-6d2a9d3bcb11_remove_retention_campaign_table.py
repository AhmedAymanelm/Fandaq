"""remove retention campaign table

Revision ID: 6d2a9d3bcb11
Revises: 9ac2d1b478ef
Create Date: 2026-04-05 17:35:00
"""

from alembic import op
import sqlalchemy as sa


revision = "6d2a9d3bcb11"
down_revision = "9ac2d1b478ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_retention_campaigns_hotel_id", table_name="retention_campaigns")
    op.drop_table("retention_campaigns")


def downgrade() -> None:
    op.create_table(
        "retention_campaigns",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.Column("inactive_days_threshold", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("offer_percent", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("offer_code", sa.String(length=50), nullable=True),
        sa.Column("targeted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_to", sa.Text(), nullable=True),
        sa.Column("failed_to", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="partial"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retention_campaigns_hotel_id", "retention_campaigns", ["hotel_id"], unique=False)
