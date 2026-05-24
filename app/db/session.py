"""Database engine and session management.

Exposes the async SQLAlchemy engine, a session factory and the
`get_session` dependency used by the API layer.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# `pool_pre_ping` transparently recycles connections dropped by the DB.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# `expire_on_commit=False` keeps ORM objects usable after commit, which is
# convenient when returning them from request handlers.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        yield session
