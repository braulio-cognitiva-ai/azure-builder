"""User schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user fields."""

    email: EmailStr
    name: Optional[str] = Field(None, max_length=255)
    role: str = Field(default="viewer", pattern=r"^(owner|admin|operator|viewer)$")


class UserCreate(UserBase):
    """Schema for creating a user."""

    azure_ad_oid: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, pattern=r"^(owner|admin|operator|viewer)$")
    avatar_url: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role."""

    role: str = Field(..., pattern=r"^(owner|admin|operator|viewer)$")


class User(UserBase):
    """Full user schema with database fields."""

    id: UUID
    tenant_id: UUID
    azure_ad_oid: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithPermissions(User):
    """User with permission flags."""

    is_owner: bool
    is_admin: bool
    can_execute: bool

    @classmethod
    def from_user(cls, user: User) -> "UserWithPermissions":
        """Create from User instance."""
        return cls(
            **user.model_dump(),
            is_owner=user.role == "owner",
            is_admin=user.role in ("owner", "admin"),
            can_execute=user.role in ("owner", "admin", "operator"),
        )
