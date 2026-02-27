"""Azure connection schemas."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.azure_connection import AuthMethod, ConnectionStatus


class AzureConnectionCreate(BaseModel):
    """Schema for creating an Azure connection."""
    subscription_id: str = Field(..., min_length=36, max_length=36)
    azure_tenant_id: str = Field(..., min_length=36, max_length=36)
    subscription_name: Optional[str] = None
    auth_method: AuthMethod = AuthMethod.SERVICE_PRINCIPAL
    
    # Service principal credentials (will be stored in Key Vault)
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class AzureConnectionUpdate(BaseModel):
    """Schema for updating an Azure connection."""
    subscription_name: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class AzureConnectionResponse(BaseModel):
    """Schema for Azure connection response."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    subscription_id: str
    azure_tenant_id: str
    subscription_name: Optional[str]
    auth_method: AuthMethod
    key_vault_ref: Optional[str]
    status: ConnectionStatus
    last_validated: Optional[datetime]
    validation_error: Optional[str]
    quotas: Optional[dict]
    metadata: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuotaInfo(BaseModel):
    """Schema for Azure subscription quota information."""
    resource_type: str
    current_usage: int
    limit: int
    unit: str
    region: Optional[str] = None


class SubscriptionQuotasResponse(BaseModel):
    """Schema for subscription quotas response."""
    subscription_id: str
    quotas: list[QuotaInfo]
    last_checked: datetime


class ExistingResource(BaseModel):
    """Schema for existing Azure resource."""
    id: str
    name: str
    type: str
    location: str
    resource_group: str
    tags: dict = Field(default_factory=dict)


class ExistingResourcesResponse(BaseModel):
    """Schema for existing resources response."""
    subscription_id: str
    total_resources: int
    resources: list[ExistingResource]
    resource_groups: list[str]
