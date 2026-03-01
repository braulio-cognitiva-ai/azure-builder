"""Deployed Resource model for tracking Azure resources."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
import enum

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Numeric, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.deployment import DeploymentRequest
    from app.models.tenant import Tenant
    from app.models.project import Project


class ResourceStatus(str, enum.Enum):
    """Resource status."""
    ACTIVE = "active"
    DELETED = "deleted"
    FAILED = "failed"
    UNKNOWN = "unknown"


class DeployedResource(Base):
    """Tracks Azure resources deployed by the platform."""
    __tablename__ = "deployed_resources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("deployment_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Azure resource info
    azure_resource_id: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_group: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Status
    status: Mapped[ResourceStatus] = mapped_column(
        SQLEnum(ResourceStatus, native_enum=False, length=20),
        nullable=False,
        default=ResourceStatus.ACTIVE,
        index=True
    )
    
    # Cost tracking
    monthly_cost_estimate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    actual_cost_mtd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    last_cost_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Drift detection
    expected_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actual_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    has_drift: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    drift_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    deployment: Mapped["DeploymentRequest"] = relationship("DeploymentRequest", back_populates="deployed_resources")
    tenant: Mapped["Tenant"] = relationship("Tenant")
    project: Mapped["Project"] = relationship("Project")
    
    def __repr__(self) -> str:
        return f"<DeployedResource(id={self.id}, name={self.name}, type={self.resource_type}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if resource is active."""
        return self.status == ResourceStatus.ACTIVE
    
    @property
    def cost_variance(self) -> Optional[Decimal]:
        """Calculate variance between estimated and actual cost."""
        if self.monthly_cost_estimate is not None and self.actual_cost_mtd is not None:
            # Project MTD to full month
            days_in_month = 30
            current_day = datetime.utcnow().day
            projected_monthly = (self.actual_cost_mtd / current_day) * days_in_month
            return projected_monthly - self.monthly_cost_estimate
        return None
