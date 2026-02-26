"""Tenant context middleware and utilities."""
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import set_tenant_context

# Context variable for storing current tenant ID
current_tenant_id: ContextVar[Optional[UUID]] = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id() -> Optional[UUID]:
    """Get the current tenant ID from context."""
    return current_tenant_id.get()


def set_current_tenant_id(tenant_id: UUID) -> None:
    """Set the current tenant ID in context."""
    current_tenant_id.set(tenant_id)


def clear_current_tenant_id() -> None:
    """Clear the current tenant ID from context."""
    current_tenant_id.set(None)


async def apply_tenant_context(db: AsyncSession, tenant_id: UUID) -> None:
    """
    Apply tenant context to database session for Row-Level Security.
    
    This MUST be called before any database operations.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
    """
    await set_tenant_context(db, str(tenant_id))
    set_current_tenant_id(tenant_id)


class TenantContextMiddleware:
    """
    Middleware to automatically set tenant context from JWT token.
    
    This ensures Row-Level Security is properly applied for all requests.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract tenant_id from request state (set by auth middleware)
        request = Request(scope)
        tenant_id = getattr(request.state, "tenant_id", None)

        if tenant_id:
            set_current_tenant_id(tenant_id)

        try:
            await self.app(scope, receive, send)
        finally:
            clear_current_tenant_id()
