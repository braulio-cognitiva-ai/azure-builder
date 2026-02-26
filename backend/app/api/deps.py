"""API dependencies (auth, db session, tenant context)."""
from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Header, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenPayload, decode_access_token, extract_token_from_header
from app.core.tenant_context import apply_tenant_context
from app.database import get_db
from app.models.user import User


async def get_current_user_token(
    authorization: Optional[str] = Header(None),
) -> TokenPayload:
    """
    Dependency to get current user from JWT token.
    
    Args:
        authorization: Authorization header
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    # Extract token from header
    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode token
    try:
        payload = decode_access_token(token)
        token_payload = TokenPayload(payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if expired
    if token_payload.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_payload


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_user_token),
) -> User:
    """
    Dependency to get current user from database.
    
    Args:
        db: Database session
        token: Token payload
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If user not found
    """
    # Apply tenant context for RLS
    await apply_tenant_context(db, token.tenant_id)

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == token.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_db_with_tenant_context(
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_user_token),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with tenant context applied.
    
    This ensures Row-Level Security is properly configured.
    
    Args:
        db: Database session
        token: Token payload
        
    Yields:
        Database session with tenant context
    """
    await apply_tenant_context(db, token.tenant_id)
    yield db


def require_role(minimum_role: str):
    """
    Dependency factory to require minimum role.
    
    Args:
        minimum_role: Minimum required role (owner, admin, operator, viewer)
        
    Returns:
        Dependency function
    """
    role_hierarchy = {
        "viewer": 1,
        "operator": 2,
        "admin": 3,
        "owner": 4,
    }

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if user has required role."""
        current_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(minimum_role, 5)

        if current_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {minimum_role}",
            )

        return current_user

    return role_checker


def require_permission(permission: str):
    """
    Dependency factory to require specific permission.
    
    Args:
        permission: Required permission (e.g., "project:create")
        
    Returns:
        Dependency function
    """
    from app.core.rbac import check_permission

    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if user has required permission."""
        if not check_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}",
            )

        return current_user

    return permission_checker


class TenantContext:
    """Tenant context extracted from token."""

    def __init__(self, token: TokenPayload):
        """Initialize from token payload."""
        self.tenant_id = token.tenant_id
        self.user_id = token.user_id
        self.user_role = token.role


async def get_tenant_context(
    token: TokenPayload = Depends(get_current_user_token),
) -> TenantContext:
    """
    Dependency to get tenant context.
    
    Args:
        token: Token payload
        
    Returns:
        Tenant context
    """
    return TenantContext(token)
