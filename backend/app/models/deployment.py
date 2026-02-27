"""Deployment request model with full state machine."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.proposal import ArchitectureProposal
    from app.models.user import User
    from app.models.deployment_resource import DeploymentResource
    from app.models.execution_log import ExecutionLog


class DeploymentStatus(str, enum.Enum):
    """Deployment lifecycle states."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    SELECTED = "selected"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PROVISIONING = "provisioning"
    DEPLOYED = "deployed"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    DECOMMISSIONED = "decommissioned"


class DeploymentRequest(Base):
    """Deployment request with full state machine.
    
    Tracks the entire lifecycle from proposal selection through
    provisioning, verification, and potential rollback/decommission.
    """
    __tablename__ = "deployment_requests"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("architecture_proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Which proposal option was selected
    selected_option_number: Mapped[int] = mapped_column(nullable=False)
    
    # Deployment status
    status: Mapped[DeploymentStatus] = mapped_column(
        SQLEnum(DeploymentStatus, native_enum=False, length=20),
        nullable=False,
        default=DeploymentStatus.DRAFT,
        index=True
    )
    
    # Generated Bicep template
    bicep_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Generated ARM JSON template
    arm_template: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Deployment parameters
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # User who created the deployment
    created_by: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"), nullable=False)
    
    # User who approved the deployment
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Deployment execution details
    azure_deployment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Error information if failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Rollback information
    rollback_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_by: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.id"), nullable=True)
    
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
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    proposal: Mapped["ArchitectureProposal"] = relationship("ArchitectureProposal", back_populates="deployments")
    resources: Mapped[list["DeploymentResource"]] = relationship("DeploymentResource", back_populates="deployment", cascade="all, delete-orphan")
    execution_logs: Mapped[list["ExecutionLog"]] = relationship("ExecutionLog", back_populates="deployment", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<DeploymentRequest(id={self.id}, status={self.status})>"
