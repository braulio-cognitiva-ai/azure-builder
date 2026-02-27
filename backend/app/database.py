"""Database connection and session management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

# Detect database type
is_sqlite = str(settings.database_url).startswith("sqlite")

# Create async engine with appropriate settings
engine_kwargs = {
    "echo": settings.database_echo,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })
else:
    # SQLite-specific settings
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })

engine = create_async_engine(str(settings.database_url), **engine_kwargs)

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
    
    For SQLite, this is a no-op (RLS not supported).
    
    Args:
        session: Database session
        tenant_id: UUID of the current tenant
    """
    if not is_sqlite:
        await session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))


async def clear_tenant_context(session: AsyncSession) -> None:
    """Clear the tenant context (use with caution)."""
    if not is_sqlite:
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
        from app import models  # noqa - Import entire models package to ensure all are registered
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # PostgreSQL-specific setup
        if not is_sqlite:
            # Enable UUID extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            
            # Enable Row-Level Security on all tenant-scoped tables
            tables_with_rls = [
                "users", "projects", "conversations", "messages",
                "audit_logs", "architecture_proposals", "deployment_requests", "azure_connections"
            ]
            
            for table in tables_with_rls:
                # Check if table exists before altering
                table_check = await conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """))
                exists = table_check.scalar()
                
                if exists:
                    await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
                    await conn.execute(text(f"""
                        DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};
                    """))
                    await conn.execute(text(f"""
                        CREATE POLICY tenant_isolation_{table} ON {table}
                        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
                    """))
        
        # Seed templates
        from app.services.template_service import TemplateService
        async with AsyncSessionLocal() as session:
            template_service = TemplateService(session)
            await template_service.seed_templates()


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
