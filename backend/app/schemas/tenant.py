"""Tenant schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TenantBase(BaseModel):
    """Base tenant fields."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    tier: str = Field(default="free", pattern=r"^(free|pro|enterprise)$")
    settings: dict[str, Any] = Field(default_factory=dict)


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""

    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tier: Optional[str] = Field(None, pattern=r"^(free|pro|enterprise)$")
    settings: Optional[dict[str, Any]] = None


class Tenant(TenantBase):
    """Full tenant schema with database fields."""

    id: UUID
    azure_key_vault_secret_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AzureConnectionCreate(BaseModel):
    """Schema for configuring Azure connection."""

    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Service Principal Client ID")
    client_secret: str = Field(..., description="Service Principal Client Secret")
    subscription_id: str = Field(..., description="Azure Subscription ID")

    @field_validator("tenant_id", "client_id", "subscription_id")
    @classmethod
    def validate_guid(cls, v: str) -> str:
        """Validate GUID format."""
        if not v or len(v) != 36:
            raise ValueError("Must be a valid GUID")
        return v

    @field_validator("client_secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        """Validate secret is not empty."""
        if not v or len(v) < 10:
            raise ValueError("Client secret must be at least 10 characters")
        return v


class AzureConnectionStatus(BaseModel):
    """Schema for Azure connection status."""

    is_configured: bool
    tenant_id: Optional[str] = None
    subscription_id: Optional[str] = None
    last_validated: Optional[datetime] = None
    validation_status: Optional[str] = None  # valid, invalid, not_tested
