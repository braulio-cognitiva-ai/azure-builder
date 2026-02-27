"""Proposal API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services import ProposalService
from app.schemas.proposal import (
    ProposalCreate,
    ProposalResponse,
    ProposalRefine,
    ProposalSelectOption,
    ProposalOptionResponse
)

router = APIRouter()


@router.post("/projects/{project_id}/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    project_id: uuid.UUID,
    data: ProposalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new architecture proposal from natural language request."""
    service = ProposalService(db)
    
    try:
        proposal = await service.create_proposal(
            project_id=project_id,
            user_request=data.user_request
        )
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create proposal: {str(e)}"
        )


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get proposal with options."""
    service = ProposalService(db)
    
    try:
        proposal = await service.get_proposal(proposal_id)
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal not found: {str(e)}"
        )


@router.get("/proposals/{proposal_id}/options", response_model=list[ProposalOptionResponse])
async def get_proposal_options(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all options for a proposal."""
    service = ProposalService(db)
    
    try:
        options = await service.get_proposal_options(proposal_id)
        return options
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal not found: {str(e)}"
        )


@router.post("/proposals/{proposal_id}/select", response_model=ProposalResponse)
async def select_option(
    proposal_id: uuid.UUID,
    data: ProposalSelectOption,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Select an option from the proposal."""
    service = ProposalService(db)
    
    try:
        proposal = await service.select_option(
            proposal_id=proposal_id,
            option_number=data.option_number
        )
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to select option: {str(e)}"
        )


@router.post("/proposals/{proposal_id}/refine", response_model=ProposalResponse)
async def refine_proposal(
    proposal_id: uuid.UUID,
    data: ProposalRefine,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Refine proposal with user feedback."""
    service = ProposalService(db)
    
    try:
        proposal = await service.refine_proposal(
            proposal_id=proposal_id,
            feedback=data.feedback
        )
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine proposal: {str(e)}"
        )
