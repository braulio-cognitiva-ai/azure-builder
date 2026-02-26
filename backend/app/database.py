"""Database connection and session management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.database_url),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """
    Set the tenant context for Row-Level Security.
    
    This MUST be called before any database operations to ensure
    proper tenant isolation via PostgreSQL RLS policies.
    
    Args:
        session: Database session
        tenant_id: UUID of the current tenant
    """
    await session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))


async def clear_tenant_context(session: AsyncSession) -> None:
    """Clear the tenant context (use with caution)."""
    await session.execute(text("SET app.current_tenant_id = ''"))


@asynccontextmanager
async def get_db_with_tenant(tenant_id: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with tenant context automatically set.
    
    Args:
        tenant_id: UUID of the current tenant
        
    Yields:
        AsyncSession: Session with tenant context configured
        
    Example:
        async with get_db_with_tenant(tenant_id) as db:
            projects = await db.execute(select(Project))
    """
    async with AsyncSessionLocal() as session:
        try:
            await set_tenant_context(session, tenant_id)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await clear_tenant_context(session)
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables if they don't exist)."""
    async with engine.begin() as conn:
        # Import all models to register them with Base
        from app.models import audit, conversation, execution, project, tenant, user  # noqa
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Enable UUID extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
        
        # Enable Row-Level Security on all tenant-scoped tables
        tables_with_rls = [
            "users", "projects", "conversations", "messages",
            "generated_commands", "executions", "audit_logs"
        ]
        
        for table in tables_with_rls:
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
            await conn.execute(text(f"""
                DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};
            """))
            await conn.execute(text(f"""
                CREATE POLICY tenant_isolation_{table} ON {table}
                USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
            """))


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
