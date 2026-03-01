"""Project model for organizing architecture work."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.database import Base
from app.db_types import UUID, ARRAY

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.proposal import ArchitectureProposal
    from app.models.conversation import Conversation


class ProjectStatus(str, enum.Enum):
    """Project lifecycle status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Project(Base):
    """Project model for organizing architecture proposals and deployments."""
    __tablename__ = "projects"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Budget constraint (monthly cost limit in USD)
    budget_limit: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus, native_enum=False, length=20),
        nullable=False,
        default=ProjectStatus.ACTIVE
    )
    
    created_by: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    
    # Tags for organization
    tags: Mapped[list] = mapped_column(ARRAY(String), nullable=False, default=list)
    
    # Custom metadata (renamed to avoid SQLAlchemy reserved word conflict)
    project_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
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
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="projects")
    creator: Mapped["User"] = relationship("User", back_populates="created_projects", foreign_keys=[created_by])
    proposals: Mapped[list["ArchitectureProposal"]] = relationship("ArchitectureProposal", back_populates="project", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"
