"""Role-Based Access Control (RBAC)."""
from enum import Enum
from fnmatch import fnmatch
from typing import Optional

from fastapi import HTTPException, status


class Role(str, Enum):
    """User roles."""

    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Permission:
    """Permission definitions."""

    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    # Execution permissions
    EXECUTION_EXECUTE = "execution:execute"
    EXECUTION_READ = "execution:read"
    EXECUTION_CANCEL = "execution:cancel"
    EXECUTION_ROLLBACK = "execution:rollback"

    # User management permissions
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Audit log permissions
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"

    # Tenant permissions
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"


# Role → Permission mapping
ROLE_PERMISSIONS: dict[Role, list[str]] = {
    Role.OWNER: ["*:*"],  # Full access
    Role.ADMIN: [
        "project:*",
        "execution:*",
        "user:read",
        "audit:read",
        "audit:export",
        "tenant:read",
    ],
    Role.OPERATOR: [
        "project:read",
        "execution:execute",
        "execution:read",
        "execution:cancel",
    ],
    Role.VIEWER: [
        "project:read",
        "execution:read",
        "user:read",
    ],
}


def check_permission(user_role: str, required_permission: str) -> bool:
    """
    Check if a user role has a specific permission.
    
    Args:
        user_role: User's role (owner, admin, operator, viewer)
        required_permission: Permission to check (e.g., "project:create")
        
    Returns:
        True if user has permission, False otherwise
    """
    try:
        role = Role(user_role)
    except ValueError:
        return False

    allowed_permissions = ROLE_PERMISSIONS.get(role, [])
    
    # Check if any allowed permission pattern matches the required permission
    return any(
        fnmatch(required_permission, pattern)
        for pattern in allowed_permissions
    )


def require_permission(user_role: str, required_permission: str) -> None:
    """
    Raise HTTP exception if user doesn't have required permission.
    
    Args:
        user_role: User's role
        required_permission: Required permission
        
    Raises:
        HTTPException: 403 if user doesn't have permission
    """
    if not check_permission(user_role, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_permission}",
        )


def require_role(user_role: str, minimum_role: Role) -> None:
    """
    Require user to have at least a specific role.
    
    Args:
        user_role: User's current role
        minimum_role: Minimum required role
        
    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    role_hierarchy = {
        Role.VIEWER: 1,
        Role.OPERATOR: 2,
        Role.ADMIN: 3,
        Role.OWNER: 4,
    }

    try:
        current_level = role_hierarchy[Role(user_role)]
        required_level = role_hierarchy[minimum_role]
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role",
        )

    if current_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient role. Required: {minimum_role.value}",
        )


class RBACChecker:
    """Dependency for checking permissions in FastAPI routes."""

    def __init__(self, required_permission: Optional[str] = None, minimum_role: Optional[Role] = None):
        """
        Initialize RBAC checker.
        
        Args:
            required_permission: Required permission (e.g., "project:create")
            minimum_role: Minimum required role
        """
        self.required_permission = required_permission
        self.minimum_role = minimum_role

    def __call__(self, user_role: str) -> bool:
        """
        Check permissions.
        
        Args:
            user_role: Current user's role
            
        Returns:
            True if authorized
            
        Raises:
            HTTPException: If not authorized
        """
        if self.required_permission:
            require_permission(user_role, self.required_permission)
        
        if self.minimum_role:
            require_role(user_role, self.minimum_role)
        
        return True
