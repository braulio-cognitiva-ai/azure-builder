"""Architecture template model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID, ARRAY

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class Template(Base):
    """Architecture template with variants.
    
    Pre-built architecture patterns that users can instantiate
    with different SKUs and configurations.
    """
    __tablename__ = "templates"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Category (e.g., "web", "microservices", "data", "ai")
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Template name
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Base architecture description (text/diagram)
    base_architecture: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Variants (JSON array of variant configurations)
    # Format: [{"name": "basic", "sku_overrides": {...}, "monthly_cost": 50}, ...]
    variants: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # List of Azure resource types used
    resource_types: Mapped[list] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Estimated monthly cost range
    estimated_cost_min: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_cost_max: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Difficulty level
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="beginner")
    
    # Is this a public template or tenant-specific?
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    
    # If tenant-specific, which tenant owns it
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Who created this template
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Tags for search/filtering
    tags: Mapped[list] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Full template data (JSON) - includes all configuration details
    template_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    tenant: Mapped["Tenant | None"] = relationship("Tenant")
    creator: Mapped["User | None"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name={self.name}, category={self.category})>"
