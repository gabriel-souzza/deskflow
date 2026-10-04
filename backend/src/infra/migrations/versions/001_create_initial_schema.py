"""create initial schema

Revision ID: 001
Revises:
Create Date: 2026-10-02 13:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cost_centers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("monthly_quota_hours", sa.Numeric(), server_default="0"),
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("cost_center_id", sa.Uuid(), sa.ForeignKey("cost_centers.id")),
        sa.Column("is_eligible_for_booking", sa.Boolean(), server_default="false"),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("floor", sa.String(), nullable=False),
        sa.Column("zone", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("resources", sa.Text(), nullable=True),
    )
    op.create_table(
        "availability_windows",
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), primary_key=True),
        sa.Column("day", sa.String(), primary_key=True),
        sa.Column("slot_index", sa.Integer(), primary_key=True),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id")),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id")),
        sa.Column("cost_center_id", sa.Uuid(), sa.ForeignKey("cost_centers.id")),
        sa.Column("slot_start", sa.DateTime(), nullable=False),
        sa.Column("slot_end", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("modified_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_table(
        "booking_windows",
        sa.Column("booking_id", sa.Uuid(), sa.ForeignKey("bookings.id"), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), primary_key=True),
        sa.Column("day", sa.String(), primary_key=True),
        sa.Column("slot_index", sa.Integer(), primary_key=True),
    )
    op.create_table(
        "quota_periods",
        sa.Column("cost_center_id", sa.Uuid(), sa.ForeignKey("cost_centers.id"), primary_key=True),
        sa.Column("period_start", sa.DateTime(), primary_key=True),
        sa.Column("period_end", sa.DateTime(), primary_key=True),
        sa.Column("total_hours", sa.Numeric(), nullable=False),
        sa.Column("consumed_hours", sa.Numeric(), nullable=False, server_default="0"),
    )
    op.create_table(
        "waitlist",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id")),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id")),
        sa.Column("desired_start", sa.DateTime(), nullable=True),
        sa.Column("desired_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("notified_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("reason", sa.String(), server_default=""),
    )
    op.create_table(
        "holidays",
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("description", sa.String(), server_default=""),
    )


def downgrade() -> None:
    op.drop_table("holidays")
    op.drop_table("audit_log")
    op.drop_table("waitlist")
    op.drop_table("cost_centers")
    op.drop_table("employees")
    op.drop_table("quota_periods")
    op.drop_table("booking_windows")
    op.drop_table("bookings")
    op.drop_table("availability_windows")
    op.drop_table("workspaces")
