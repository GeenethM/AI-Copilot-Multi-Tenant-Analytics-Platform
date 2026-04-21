"""
rls.py
──────
PostgreSQL Row-Level Security (RLS) helpers.

What is RLS?
  RLS is a PostgreSQL feature that lets you attach a security policy directly
  to a table. When a policy is active, PostgreSQL automatically adds a WHERE
  clause to every query on that table — even if the application code forgets
  to filter by tenant.

How we use it here:
  1. Each tenant-scoped table has a policy:
         CREATE POLICY tenant_isolation ON <table>
         USING (tenant_id = current_setting('app.tenant_id')::uuid);

  2. Before any database operation in a request, we set the session variable:
         SET LOCAL app.tenant_id = '<uuid>';

  3. PostgreSQL then enforces that every read/write on that table is scoped
     to the correct tenant — even if the repository forgets to filter.

  4. The 'tenants' table itself is NOT RLS-protected (it's managed by admins).

Usage in a FastAPI route:
    async with set_tenant_context(db, tenant_id):
        documents = await document_repo.list_all(db)
        # ↑ PostgreSQL automatically adds WHERE tenant_id = '<tenant_id>'
"""

from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def set_tenant_context(db: AsyncSession, tenant_id: UUID):
    """
    Async context manager that sets the PostgreSQL session variable used by RLS.

    Must be used around any database operation that reads/writes tenant data.

    Args:
        db:        The active async SQLAlchemy session.
        tenant_id: The UUID of the tenant making the request.

    Example:
        async with set_tenant_context(db, tenant_id):
            result = await document_repo.list_all(db)
    """
    await db.execute(
        text("SET LOCAL app.tenant_id = :tenant_id"),
        {"tenant_id": str(tenant_id)},
    )
    yield


async def apply_rls_policies(db: AsyncSession) -> None:
    """
    Creates RLS policies on all tenant-scoped tables.

    Call this once during database initialisation (after running migrations).
    Safe to call multiple times — uses CREATE POLICY IF NOT EXISTS pattern
    via DO blocks.

    Tables covered: uploaded_documents, ml_models, chat_sessions,
                    chat_messages, prediction_logs
    """
    tenant_tables = [
        "uploaded_documents",
        "ml_models",
        "chat_sessions",
        "chat_messages",
        "prediction_logs",
    ]

    for table in tenant_tables:
        await db.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        await db.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        # Drop existing policy first so this function is idempotent
        await db.execute(
            text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies
                        WHERE tablename = '{table}'
                        AND policyname = 'tenant_isolation'
                    ) THEN
                        EXECUTE $policy$
                            CREATE POLICY tenant_isolation ON {table}
                            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
                            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
                        $policy$;
                    END IF;
                END$$;
                """
            )
        )

    await db.commit()
