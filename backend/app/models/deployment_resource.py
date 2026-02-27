"""Deployment resource model - tracks individual Azure resources."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
import enum

from sqlalchemy import String, DateTime, ForeignKey, func, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.deployment import DeploymentRequest


class ResourceStatus(str, enum.Enum):
    """Individual resource provisioning status."""
    PENDING = "pending"
    CREATING = "creating"
    CREATED = "created"
    FAILED = "failed"
    DELETED = "deleted"


class DeploymentResource(Base):
    """Individual Azure resource within a deployment.
    
    Tracks each resource's provisioning status, Azure ID,
    and cost information.
    """
    __tablename__ = "deployment_resources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("deployment_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Azure resource ID (once provisioned)
    azure_resource_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    
    # Resource type (e.g., "Microsoft.Web/sites", "Microsoft.Sql/servers")
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Resource name
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # SKU/tier
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Region
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Status
    status: Mapped[ResourceStatus] = mapped_column(
        SQLEnum(ResourceStatus, native_enum=False, length=20),
        nullable=False,
        default=ResourceStatus.PENDING
    )
    
    # Monthly cost estimate
    monthly_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Additional resource properties (tags, configuration, etc.)
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Error message if failed
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
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
    deployment: Mapped["DeploymentRequest"] = relationship("DeploymentRequest", back_populates="resources")
    
    def __repr__(self) -> str:
        return f"<DeploymentResource(id={self.id}, name={self.name}, type={self.resource_type}, status={self.status})>"
