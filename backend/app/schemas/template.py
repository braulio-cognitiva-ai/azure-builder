"""Template schemas."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    """Schema for creating a template."""
    category: str
    name: str
    description: str
    base_architecture: str
    variants: dict = Field(default_factory=dict)
    resource_types: list[str] = Field(default_factory=list)
    estimated_cost_min: Optional[str] = None
    estimated_cost_max: Optional[str] = None
    difficulty: str = "beginner"
    tags: list[str] = Field(default_factory=list)
    template_data: dict = Field(default_factory=dict)
    is_public: bool = False


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    category: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    base_architecture: Optional[str] = None
    variants: Optional[dict] = None
    resource_types: Optional[list[str]] = None
    estimated_cost_min: Optional[str] = None
    estimated_cost_max: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None
    template_data: Optional[dict] = None


class TemplateResponse(BaseModel):
    """Schema for template response."""
    id: uuid.UUID
    category: str
    name: str
    description: str
    base_architecture: str
    variants: dict
    resource_types: list[str]
    estimated_cost_min: Optional[str]
    estimated_cost_max: Optional[str]
    difficulty: str
    is_public: bool
    tenant_id: Optional[uuid.UUID]
    created_by: Optional[uuid.UUID]
    tags: list[str]
    template_data: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateCategoryResponse(BaseModel):
    """Schema for template category summary."""
    category: str
    count: int
    templates: list[TemplateResponse] = []
