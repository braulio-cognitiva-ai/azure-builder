"""Architecture proposal model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.proposal_option import ProposalOption
    from app.models.deployment import DeploymentRequest


class ProposalStatus(str, enum.Enum):
    """Proposal generation status."""
    GENERATING = "generating"
    READY = "ready"
    SELECTED = "selected"
    FAILED = "failed"


class ArchitectureProposal(Base):
    """Architecture proposal with multiple options.
    
    Stores the user's natural language request and the AI-generated
    architecture options with pricing and diagrams.
    """
    __tablename__ = "architecture_proposals"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # User's natural language request
    user_request: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status of proposal generation
    status: Mapped[ProposalStatus] = mapped_column(
        SQLEnum(ProposalStatus, native_enum=False, length=20),
        nullable=False,
        default=ProposalStatus.GENERATING
    )
    
    # Which option was selected (1, 2, or 3)
    selected_option: Mapped[int | None] = mapped_column(nullable=True)
    
    # Error message if generation failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
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
    project: Mapped["Project"] = relationship("Project", back_populates="proposals")
    options: Mapped[list["ProposalOption"]] = relationship("ProposalOption", back_populates="proposal", cascade="all, delete-orphan")
    deployments: Mapped[list["DeploymentRequest"]] = relationship("DeploymentRequest", back_populates="proposal", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<ArchitectureProposal(id={self.id}, status={self.status}, options={len(self.options)})>"
