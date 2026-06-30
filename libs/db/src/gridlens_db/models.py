from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

naming_convention = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(schema="app", naming_convention=naming_convention)

uuid_pk = UUID(as_uuid=True)
timestamp = DateTime(timezone=True)

tenants = Table(
    "tenants",
    metadata,
    Column("id", uuid_pk, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("name", Text, nullable=False),
    Column("slug", Text, nullable=False),
    Column("status", String(32), nullable=False, server_default=text("'active'")),
    Column("preferences_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("created_at", timestamp, nullable=False, server_default=text("now()")),
    Column("updated_at", timestamp, nullable=False, server_default=text("now()")),
    CheckConstraint(
        "status in ('active', 'suspended', 'archived')",
        name="tenant_status",
    ),
    UniqueConstraint("slug"),
)

app_users = Table(
    "app_users",
    metadata,
    Column("id", uuid_pk, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("email", Text, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("external_auth_provider", Text, nullable=False),
    Column("external_subject", Text, nullable=False),
    Column("status", String(32), nullable=False, server_default=text("'active'")),
    Column("created_at", timestamp, nullable=False, server_default=text("now()")),
    Column("updated_at", timestamp, nullable=False, server_default=text("now()")),
    CheckConstraint(
        "status in ('active', 'invited', 'disabled')",
        name="app_user_status",
    ),
    UniqueConstraint("email"),
    UniqueConstraint("external_auth_provider", "external_subject"),
)

tenant_memberships = Table(
    "tenant_memberships",
    metadata,
    Column("id", uuid_pk, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("tenant_id", uuid_pk, ForeignKey("app.tenants.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", uuid_pk, ForeignKey("app.app_users.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(64), nullable=False),
    Column("status", String(32), nullable=False, server_default=text("'active'")),
    Column("invited_at", timestamp),
    Column("joined_at", timestamp),
    Column("created_at", timestamp, nullable=False, server_default=text("now()")),
    Column("updated_at", timestamp, nullable=False, server_default=text("now()")),
    CheckConstraint(
        "role in ('tenant_admin', 'program_manager', 'analyst', 'viewer')",
        name="tenant_membership_role",
    ),
    CheckConstraint(
        "status in ('invited', 'active', 'disabled')",
        name="tenant_membership_status",
    ),
    UniqueConstraint("tenant_id", "user_id"),
)
Index("ix_tenant_memberships_tenant_id_role", tenant_memberships.c.tenant_id, tenant_memberships.c.role)
Index("ix_tenant_memberships_user_id", tenant_memberships.c.user_id)

file_objects = Table(
    "file_objects",
    metadata,
    Column("id", uuid_pk, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("tenant_id", uuid_pk, ForeignKey("app.tenants.id", ondelete="CASCADE"), nullable=False),
    Column("created_by_user_id", uuid_pk, ForeignKey("app.app_users.id", ondelete="SET NULL")),
    Column("object_purpose", String(64), nullable=False),
    Column("original_file_name", Text, nullable=False),
    Column("content_type", Text, nullable=False),
    Column("storage_bucket", Text, nullable=False),
    Column("storage_key", Text, nullable=False),
    Column("checksum_sha256", String(64), nullable=False),
    Column("file_size_bytes", BigInteger, nullable=False),
    Column("storage_status", String(32), nullable=False, server_default=text("'available'")),
    Column("created_at", timestamp, nullable=False, server_default=text("now()")),
    Column("updated_at", timestamp, nullable=False, server_default=text("now()")),
    CheckConstraint(
        "object_purpose in ('dataset_upload', 'assistant_document', 'report_export')",
        name="file_object_purpose",
    ),
    CheckConstraint(
        "storage_status in ('pending', 'available', 'deleted')",
        name="file_object_storage_status",
    ),
    CheckConstraint("file_size_bytes >= 0", name="file_object_size_nonnegative"),
    UniqueConstraint("tenant_id", "storage_bucket", "storage_key"),
)
Index("ix_file_objects_tenant_id_created_at", file_objects.c.tenant_id, file_objects.c.created_at)
Index("ix_file_objects_tenant_id_object_purpose", file_objects.c.tenant_id, file_objects.c.object_purpose)

audit_logs = Table(
    "audit_logs",
    metadata,
    Column("id", uuid_pk, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("tenant_id", uuid_pk, ForeignKey("app.tenants.id", ondelete="CASCADE"), nullable=False),
    Column("actor_user_id", uuid_pk, ForeignKey("app.app_users.id", ondelete="SET NULL")),
    Column("action", String(128), nullable=False),
    Column("outcome", String(32), nullable=False),
    Column("severity", String(32), nullable=False, server_default=text("'info'")),
    Column("target_type", String(128)),
    Column("target_id", Text),
    Column("request_id", Text),
    Column("metadata_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("created_at", timestamp, nullable=False, server_default=text("now()")),
    CheckConstraint(
        "outcome in ('success', 'denied', 'failure')",
        name="audit_log_outcome",
    ),
    CheckConstraint(
        "severity in ('debug', 'info', 'warning', 'error')",
        name="audit_log_severity",
    ),
)
Index("ix_audit_logs_tenant_id_created_at", audit_logs.c.tenant_id, audit_logs.c.created_at)
Index("ix_audit_logs_tenant_id_action", audit_logs.c.tenant_id, audit_logs.c.action)
