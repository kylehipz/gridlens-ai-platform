"""create platform role assignments

Revision ID: 20260702_0004
Revises: 20260630_0003
Create Date: 2026-07-02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260702_0004"
down_revision = "20260630_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_role_assignments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=32), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role in ('Platform Admin', 'Platform Operator')",
            name=op.f("ck_platform_role_assignments_platform_role_assignment_role"),
        ),
        sa.CheckConstraint(
            "status in ('active', 'disabled')",
            name=op.f("ck_platform_role_assignments_platform_role_assignment_status"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app.app_users.id"],
            name=op.f("fk_platform_role_assignments_user_id_app_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_role_assignments")),
        sa.UniqueConstraint(
            "user_id",
            "role",
            name=op.f("uq_platform_role_assignments_user_id_role"),
        ),
        schema="app",
    )
    op.create_index(
        "ix_platform_role_assignments_user_id_status",
        "platform_role_assignments",
        ["user_id", "status"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_platform_role_assignments_user_id_status",
        table_name="platform_role_assignments",
        schema="app",
    )
    op.drop_table("platform_role_assignments", schema="app")
