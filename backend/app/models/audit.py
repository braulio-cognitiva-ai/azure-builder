"""Audit log model for compliance and tracking."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID, INET

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class AuditAction(str, enum.Enum):
    """Audit action types."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # Projects
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    
    # Proposals
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_OPTION_SELECTED = "proposal_option_selected"
    PROPOSAL_REFINED = "proposal_refined"
    
    # Deployments
    DEPLOYMENT_CREATED = "deployment_created"
    DEPLOYMENT_APPROVED = "deployment_approved"
    DEPLOYMENT_EXECUTED = "deployment_executed"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    DEPLOYMENT_ROLLED_BACK = "deployment_rolled_back"
    
    # Azure Connections
    AZURE_CONNECTION_ADDED = "azure_connection_added"
    AZURE_CONNECTION_VALIDATED = "azure_connection_validated"
    AZURE_CONNECTION_REMOVED = "azure_connection_removed"
    
    # Users
    USER_INVITED = "user_invited"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_REMOVED = "user_removed"
    
    # Settings
    SETTINGS_UPDATED = "settings_updated"
    
    # Templates
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"


class AuditLog(Base):
    """Audit log for all significant actions.
    
    Provides immutable audit trail for compliance and debugging.
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Action type
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, native_enum=False, length=50),
        nullable=False,
        index=True
    )
    
    # Entity type (e.g., "project", "deployment", "user")
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Entity ID (UUID of the affected resource)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True, index=True)
    
    # Additional details (JSON)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(INET(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="audit_logs")
    user: Mapped["User | None"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, entity_type={self.entity_type})>"
