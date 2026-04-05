"""add email to user model

Revision ID: 8e1c4d4a7f3b
Revises: 9f2c6b1ad4e2
Create Date: 2026-04-05 12:15:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8e1c4d4a7f3b"
down_revision = "9f2c6b1ad4e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "email")
