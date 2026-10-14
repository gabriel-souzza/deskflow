"""Add role column to employees table.

Revision ID: 003
Revises: 002
Create Date: 2026-10-13 21:22:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("role", sa.String(), nullable=False, server_default="employee"),
    )
    op.execute("UPDATE employees SET role = 'admin' WHERE email = 'admin@deskflow.com'")


def downgrade() -> None:
    op.drop_column("employees", "role")
