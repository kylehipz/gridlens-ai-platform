"""add initial rls policies

Revision ID: 20260630_0003
Revises: 20260630_0002
Create Date: 2026-06-30
"""

from alembic import op

revision = "20260630_0003"
down_revision = "20260630_0002"
branch_labels = None
depends_on = None

TENANT_POLICY_TABLES = {
    "tenants": "id",
    "tenant_memberships": "tenant_id",
    "file_objects": "tenant_id",
    "audit_logs": "tenant_id",
}


def _tenant_setting_expression(column_name: str) -> str:
    return f"{column_name} = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    for table_name, tenant_column in TENANT_POLICY_TABLES.items():
        policy_expression = _tenant_setting_expression(tenant_column)
        op.execute(f"ALTER TABLE app.{table_name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE app.{table_name} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table_name}_tenant_isolation
            ON app.{table_name}
            USING ({policy_expression})
            WITH CHECK ({policy_expression})
            """
        )


def downgrade() -> None:
    for table_name in reversed(TENANT_POLICY_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table_name}_tenant_isolation ON app.{table_name}")
        op.execute(f"ALTER TABLE app.{table_name} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE app.{table_name} DISABLE ROW LEVEL SECURITY")
