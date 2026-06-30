"""create identity file audit schema

Revision ID: 20260630_0002
Revises: 20260630_0001
Create Date: 2026-06-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260630_0002"
down_revision = "20260630_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(length=32), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column(
            "preferences_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
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
            "status in ('active', 'suspended', 'archived')", name="ck_tenants_tenant_status"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
        schema="app",
    )
    op.create_table(
        "app_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("external_auth_provider", sa.Text(), nullable=False),
        sa.Column("external_subject", sa.Text(), nullable=False),
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
            "status in ('active', 'invited', 'disabled')", name="ck_app_users_app_user_status"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_users"),
        sa.UniqueConstraint("email", name="uq_app_users_email"),
        sa.UniqueConstraint(
            "external_auth_provider",
            "external_subject",
            name="uq_app_users_external_auth_provider_external_subject",
        ),
        schema="app",
    )
    op.create_table(
        "tenant_memberships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=32), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
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
            "role in ('tenant_admin', 'program_manager', 'analyst', 'viewer')",
            name="ck_tenant_memberships_tenant_membership_role",
        ),
        sa.CheckConstraint(
            "status in ('invited', 'active', 'disabled')",
            name="ck_tenant_memberships_tenant_membership_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["app.tenants.id"],
            name="fk_tenant_memberships_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app.app_users.id"],
            name="fk_tenant_memberships_user_id_app_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_memberships"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_id_user_id"),
        schema="app",
    )
    op.create_index(
        "ix_tenant_memberships_tenant_id_role",
        "tenant_memberships",
        ["tenant_id", "role"],
        schema="app",
    )
    op.create_index(
        "ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"], schema="app"
    )
    op.create_table(
        "file_objects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("object_purpose", sa.String(length=64), nullable=False),
        sa.Column("original_file_name", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("storage_bucket", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "storage_status",
            sa.String(length=32),
            server_default=sa.text("'available'"),
            nullable=False,
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
            "object_purpose in ('dataset_upload', 'assistant_document', 'report_export')",
            name="ck_file_objects_file_object_purpose",
        ),
        sa.CheckConstraint(
            "storage_status in ('pending', 'available', 'deleted')",
            name="ck_file_objects_file_object_storage_status",
        ),
        sa.CheckConstraint(
            "file_size_bytes >= 0", name="ck_file_objects_file_object_size_nonnegative"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["app.app_users.id"],
            name="fk_file_objects_created_by_user_id_app_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["app.tenants.id"],
            name="fk_file_objects_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_file_objects"),
        sa.UniqueConstraint(
            "tenant_id",
            "storage_bucket",
            "storage_key",
            name="uq_file_objects_tenant_id_storage_bucket_storage_key",
        ),
        schema="app",
    )
    op.create_index(
        "ix_file_objects_tenant_id_created_at",
        "file_objects",
        ["tenant_id", "created_at"],
        schema="app",
    )
    op.create_index(
        "ix_file_objects_tenant_id_object_purpose",
        "file_objects",
        ["tenant_id", "object_purpose"],
        schema="app",
    )
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column(
            "severity", sa.String(length=32), server_default=sa.text("'info'"), nullable=False
        ),
        sa.Column("target_type", sa.String(length=128), nullable=True),
        sa.Column("target_id", sa.Text(), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome in ('success', 'denied', 'failure')", name="ck_audit_logs_audit_log_outcome"
        ),
        sa.CheckConstraint(
            "severity in ('debug', 'info', 'warning', 'error')",
            name="ck_audit_logs_audit_log_severity",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["app.app_users.id"],
            name="fk_audit_logs_actor_user_id_app_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["app.tenants.id"],
            name="fk_audit_logs_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        schema="app",
    )
    op.create_index(
        "ix_audit_logs_tenant_id_action", "audit_logs", ["tenant_id", "action"], schema="app"
    )
    op.create_index(
        "ix_audit_logs_tenant_id_created_at",
        "audit_logs",
        ["tenant_id", "created_at"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_tenant_id_created_at", table_name="audit_logs", schema="app")
    op.drop_index("ix_audit_logs_tenant_id_action", table_name="audit_logs", schema="app")
    op.drop_table("audit_logs", schema="app")
    op.drop_index(
        "ix_file_objects_tenant_id_object_purpose", table_name="file_objects", schema="app"
    )
    op.drop_index("ix_file_objects_tenant_id_created_at", table_name="file_objects", schema="app")
    op.drop_table("file_objects", schema="app")
    op.drop_index("ix_tenant_memberships_user_id", table_name="tenant_memberships", schema="app")
    op.drop_index(
        "ix_tenant_memberships_tenant_id_role", table_name="tenant_memberships", schema="app"
    )
    op.drop_table("tenant_memberships", schema="app")
    op.drop_table("app_users", schema="app")
    op.drop_table("tenants", schema="app")
