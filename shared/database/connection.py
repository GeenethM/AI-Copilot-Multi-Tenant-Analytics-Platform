"""
connection.py
─────────────
Async SQLAlchemy engine and session factory.

Every service imports get_db() and uses it as a FastAPI dependency:

    from shared.database.connection import get_db

    @router.get("/something")
    async def handler(db: AsyncSession = Depends(get_db)):
        ...

The DATABASE_URL must use the asyncpg driver:
    postgresql+asyncpg://user:password@host:5432/dbname

How connection pooling works:
  - pool_size:    Up to 10 connections kept alive (reused across requests)
  - max_overflow: Up to 20 extra connections allowed under heavy load
  - pool_pre_ping: Tests connections before use (handles DB restarts gracefully)
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.database.config import get_db_settings

_settings = get_db_settings()

engine = create_async_engine(
    _settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    # echo=True logs every SQL statement — useful for debugging, disable in prod
    echo=_settings.database_echo,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keeps ORM objects usable after commit
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Usage:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            result = await tenant_repo.get_by_id(db, tenant_id)

    The session is automatically closed when the request is done,
    and rolled back if an exception is raised.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
