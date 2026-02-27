"""Deployment schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from app.models.deployment import DeploymentStatus
from app.models.deployment_resource import ResourceStatus
from app.models.execution_log import LogLevel


class DeploymentCreate(BaseModel):
    """Schema for creating a deployment."""
    proposal_id: uuid.UUID
    selected_option_number: int = Field(..., ge=1, le=3)
    parameters: dict = Field(default_factory=dict)


class DeploymentApprove(BaseModel):
    """Schema for approving a deployment."""
    confirmation: bool = Field(True, description="User must confirm approval")


class DeploymentResourceResponse(BaseModel):
    """Schema for deployment resource response."""
    id: uuid.UUID
    deployment_id: uuid.UUID
    azure_resource_id: Optional[str]
    resource_type: str
    name: str
    sku: Optional[str]
    region: str
    status: ResourceStatus
    monthly_cost: Optional[Decimal]
    properties: dict
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExecutionLogResponse(BaseModel):
    """Schema for execution log response."""
    id: uuid.UUID
    deployment_id: uuid.UUID
    sequence: int
    level: LogLevel
    message: str
    source: Optional[str]
    resource_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeploymentResponse(BaseModel):
    """Schema for deployment response."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    proposal_id: uuid.UUID
    selected_option_number: int
    status: DeploymentStatus
    bicep_template: Optional[str]
    arm_template: Optional[dict]
    parameters: dict
    created_by: uuid.UUID
    approved_by: Optional[uuid.UUID]
    approved_at: Optional[datetime]
    azure_deployment_id: Optional[str]
    resource_group_name: Optional[str]
    error_message: Optional[str]
    error_details: Optional[dict]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    resources: list[DeploymentResourceResponse] = []
    
    class Config:
        from_attributes = True


class DeploymentReview(BaseModel):
    """Schema for deployment review information."""
    deployment: DeploymentResponse
    total_resources: int
    total_monthly_cost: Decimal
    resource_breakdown: list[dict]
    warnings: list[str] = []
    
    class Config:
        from_attributes = True
