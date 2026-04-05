"""add review reply workflow

Revision ID: 4f91ab2c7d10
Revises: c1b3a92d8f44
Create Date: 2026-04-05 15:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "4f91ab2c7d10"
down_revision = "c1b3a92d8f44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("sentiment", sa.String(length=20), nullable=False, server_default="neutral"))
    op.add_column("reviews", sa.Column("reply_status", sa.String(length=30), nullable=False, server_default="pending_approval"))
    op.add_column("reviews", sa.Column("final_reply_text", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("reply_generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reviews", sa.Column("reply_approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reviews", sa.Column("reply_approved_by_user_id", sa.UUID(), nullable=True))
    op.add_column("reviews", sa.Column("reply_approved_by_name", sa.String(length=255), nullable=True))
    op.add_column("reviews", sa.Column("reply_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reviews", sa.Column("reply_sent_channel", sa.String(length=30), nullable=True))

    op.create_index("ix_reviews_sentiment", "reviews", ["sentiment"], unique=False)
    op.create_index("ix_reviews_reply_status", "reviews", ["reply_status"], unique=False)
    op.create_index("ix_reviews_reply_approved_by_user_id", "reviews", ["reply_approved_by_user_id"], unique=False)
    op.create_foreign_key(
        "fk_reviews_reply_approved_by_user_id",
        "reviews",
        "users",
        ["reply_approved_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_reviews_reply_approved_by_user_id", "reviews", type_="foreignkey")
    op.drop_index("ix_reviews_reply_approved_by_user_id", table_name="reviews")
    op.drop_index("ix_reviews_reply_status", table_name="reviews")
    op.drop_index("ix_reviews_sentiment", table_name="reviews")

    op.drop_column("reviews", "reply_sent_channel")
    op.drop_column("reviews", "reply_sent_at")
    op.drop_column("reviews", "reply_approved_by_name")
    op.drop_column("reviews", "reply_approved_by_user_id")
    op.drop_column("reviews", "reply_approved_at")
    op.drop_column("reviews", "reply_generated_at")
    op.drop_column("reviews", "final_reply_text")
    op.drop_column("reviews", "reply_status")
    op.drop_column("reviews", "sentiment")
