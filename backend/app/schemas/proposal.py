"""Proposal schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from app.models.proposal import ProposalStatus


class CostEstimate(BaseModel):
    """Cost estimate for a single resource."""
    service: str = Field(..., description="Azure service name")
    sku: str = Field(..., description="SKU/tier")
    region: str = Field(..., description="Azure region")
    quantity: int = Field(1, description="Number of instances")
    unit_price: Decimal = Field(..., description="Unit price per hour/month")
    monthly_cost: Decimal = Field(..., description="Estimated monthly cost")
    unit: str = Field("instance", description="Unit of measure")


class ResourceDefinition(BaseModel):
    """Definition of an Azure resource in a proposal option."""
    type: str = Field(..., description="Resource type (e.g., 'App Service')")
    name: str = Field(..., description="Resource name")
    sku: str = Field(..., description="SKU/tier")
    region: str = Field(..., description="Azure region")
    properties: dict = Field(default_factory=dict, description="Additional properties")


class ProsCons(BaseModel):
    """Pros and cons for a proposal option."""
    pros: list[str] = Field(default_factory=list, description="Advantages")
    cons: list[str] = Field(default_factory=list, description="Disadvantages")


class ProposalOptionCreate(BaseModel):
    """Schema for creating a proposal option."""
    option_number: int
    name: str
    description: str
    architecture_diagram: str
    resources: list[ResourceDefinition]
    cost_estimates: list[CostEstimate]
    pros_cons: ProsCons
    monthly_cost: Decimal


class ProposalOptionResponse(BaseModel):
    """Schema for proposal option response."""
    id: uuid.UUID
    proposal_id: uuid.UUID
    option_number: int
    name: str
    description: str
    architecture_diagram: str
    resources_json: dict
    cost_estimate_json: dict
    pros_cons_json: dict
    monthly_cost: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProposalCreate(BaseModel):
    """Schema for creating a proposal."""
    project_id: uuid.UUID
    user_request: str = Field(..., min_length=10, max_length=5000)


class ProposalRefine(BaseModel):
    """Schema for refining a proposal."""
    feedback: str = Field(..., min_length=10, max_length=2000)


class ProposalSelectOption(BaseModel):
    """Schema for selecting a proposal option."""
    option_number: int = Field(..., ge=1, le=3)


class ProposalResponse(BaseModel):
    """Schema for proposal response."""
    id: uuid.UUID
    project_id: uuid.UUID
    tenant_id: uuid.UUID
    user_request: str
    status: ProposalStatus
    selected_option: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    options: list[ProposalOptionResponse] = []
    
    class Config:
        from_attributes = True
