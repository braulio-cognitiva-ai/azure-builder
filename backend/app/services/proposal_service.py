"""Proposal Service - Manages architecture proposals."""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import ArchitectureProposal, ProposalOption, ProposalStatus, Project
from app.services.ai_engine import AIEngineService


class ProposalService:
    """Service for managing architecture proposals."""
    
    def __init__(self, session: AsyncSession):
        """Initialize proposal service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.ai_engine = AIEngineService(session)
    
    async def create_proposal(
        self,
        project_id: uuid.UUID,
        user_request: str,
        context: Optional[dict] = None
    ) -> ArchitectureProposal:
        """Create a new architecture proposal.
        
        Args:
            project_id: Project ID
            user_request: User's natural language request
            context: Optional context (budget, existing infra, etc.)
        
        Returns:
            Created proposal with options
        """
        # Get project
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        project = result.scalar_one()
        
        # Generate proposal using AI engine
        proposal = await self.ai_engine.generate_proposal(
            project=project,
            user_request=user_request,
            context=context
        )
        
        return proposal
    
    async def get_proposal(
        self,
        proposal_id: uuid.UUID
    ) -> ArchitectureProposal:
        """Get proposal with options.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            Proposal with options loaded
        """
        stmt = select(ArchitectureProposal).where(
            ArchitectureProposal.id == proposal_id
        ).options(
            selectinload(ArchitectureProposal.options)
        )
        
        result = await self.session.execute(stmt)
        proposal = result.scalar_one()
        
        return proposal
    
    async def get_proposal_options(
        self,
        proposal_id: uuid.UUID
    ) -> list[ProposalOption]:
        """Get all options for a proposal.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            List of proposal options
        """
        stmt = select(ProposalOption).where(
            ProposalOption.proposal_id == proposal_id
        ).order_by(ProposalOption.option_number)
        
        result = await self.session.execute(stmt)
        options = result.scalars().all()
        
        return list(options)
    
    async def select_option(
        self,
        proposal_id: uuid.UUID,
        option_number: int
    ) -> ArchitectureProposal:
        """Select an option from the proposal.
        
        Args:
            proposal_id: Proposal ID
            option_number: Option number to select (1-3)
        
        Returns:
            Updated proposal
        """
        stmt = select(ArchitectureProposal).where(
            ArchitectureProposal.id == proposal_id
        )
        result = await self.session.execute(stmt)
        proposal = result.scalar_one()
        
        # Validate option exists
        stmt = select(ProposalOption).where(
            ProposalOption.proposal_id == proposal_id,
            ProposalOption.option_number == option_number
        )
        result = await self.session.execute(stmt)
        option = result.scalar_one()  # Will raise if not found
        
        # Update proposal
        proposal.selected_option = option_number
        proposal.status = ProposalStatus.SELECTED
        
        await self.session.commit()
        await self.session.refresh(proposal)
        
        return proposal
    
    async def refine_proposal(
        self,
        proposal_id: uuid.UUID,
        feedback: str
    ) -> ArchitectureProposal:
        """Refine proposal based on user feedback.
        
        Args:
            proposal_id: Proposal ID
            feedback: User's refinement feedback
        
        Returns:
            Updated proposal with new options
        """
        stmt = select(ArchitectureProposal).where(
            ArchitectureProposal.id == proposal_id
        )
        result = await self.session.execute(stmt)
        proposal = result.scalar_one()
        
        # Use AI engine to refine
        proposal = await self.ai_engine.refine_proposal(proposal, feedback)
        
        return proposal
