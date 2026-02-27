"""Proposal option model - individual architecture options."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.proposal import ArchitectureProposal


class ProposalOption(Base):
    """Individual architecture option within a proposal.
    
    Each proposal has 2-3 options with different approaches,
    SKUs, and cost estimates.
    """
    __tablename__ = "proposal_options"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("architecture_proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Option number (1, 2, 3)
    option_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Option name (e.g., "Basic Web App", "Scalable Microservices")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Detailed description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ASCII architecture diagram
    architecture_diagram: Mapped[str] = mapped_column(Text, nullable=False)
    
    # List of Azure resources with SKUs (JSON)
    # Format: [{"type": "App Service", "name": "app-main", "sku": "P1V2", "region": "eastus"}]
    resources_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Cost estimate breakdown (JSON)
    # Format: [{"service": "App Service", "sku": "P1V2", "monthly_cost": 100.50, "unit": "instance"}]
    cost_estimate_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Pros and cons (JSON)
    # Format: {"pros": ["Fast deployment", "Cost-effective"], "cons": ["Limited scalability"]}
    pros_cons_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Total monthly cost estimate
    monthly_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # Relationships
    proposal: Mapped["ArchitectureProposal"] = relationship("ArchitectureProposal", back_populates="options")
    
    def __repr__(self) -> str:
        return f"<ProposalOption(id={self.id}, name={self.name}, cost=${self.monthly_cost}/mo)>"
