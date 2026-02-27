"""Deployment API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services import DeploymentService
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentResponse,
    DeploymentApprove,
    DeploymentReview,
    ExecutionLogResponse
)

router = APIRouter()


@router.post("/proposals/{proposal_id}/deploy", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    proposal_id: uuid.UUID,
    data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create deployment from selected proposal option."""
    service = DeploymentService(db)
    
    try:
        deployment = await service.create_deployment(
            proposal_id=proposal_id,
            selected_option_number=data.selected_option_number,
            created_by=current_user.id,
            parameters=data.parameters
        )
        return deployment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create deployment: {str(e)}"
        )


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get deployment status and details."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models import DeploymentRequest
    
    stmt = select(DeploymentRequest).where(
        DeploymentRequest.id == deployment_id
    ).options(
        selectinload(DeploymentRequest.resources)
    )
    
    result = await db.execute(stmt)
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    return deployment


@router.get("/deployments/{deployment_id}/review", response_model=DeploymentReview)
async def review_deployment(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get deployment review information before approval."""
    service = DeploymentService(db)
    
    try:
        review = await service.review_deployment(deployment_id)
        return review
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment not found: {str(e)}"
        )


@router.post("/deployments/{deployment_id}/approve", response_model=DeploymentResponse)
async def approve_deployment(
    deployment_id: uuid.UUID,
    data: DeploymentApprove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve deployment for execution."""
    service = DeploymentService(db)
    
    try:
        deployment = await service.approve_deployment(
            deployment_id=deployment_id,
            approved_by=current_user.id
        )
        return deployment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve deployment: {str(e)}"
        )


@router.post("/deployments/{deployment_id}/execute", response_model=DeploymentResponse)
async def execute_deployment(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute approved deployment (provision resources)."""
    service = DeploymentService(db)
    
    try:
        deployment = await service.execute_deployment(deployment_id)
        return deployment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute deployment: {str(e)}"
        )


@router.post("/deployments/{deployment_id}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rollback deployment (delete resources)."""
    service = DeploymentService(db)
    
    try:
        deployment = await service.rollback_deployment(
            deployment_id=deployment_id,
            rolled_back_by=current_user.id
        )
        return deployment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback deployment: {str(e)}"
        )


@router.get("/deployments/{deployment_id}/logs", response_model=list[ExecutionLogResponse])
async def get_execution_logs(
    deployment_id: uuid.UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get real-time execution logs for deployment."""
    service = DeploymentService(db)
    
    try:
        logs = await service.get_execution_logs(deployment_id, limit=limit)
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment not found: {str(e)}"
        )
