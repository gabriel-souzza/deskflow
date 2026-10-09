"""Add employee account credentials and unique email constraint."""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("password_hash", sa.String(), nullable=True))
    op.create_unique_constraint("uq_employees_email", "employees", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_employees_email", "employees", type_="unique")
    op.drop_column("employees", "password_hash")
