"""Template API routes."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services import TemplateService
from app.schemas.template import TemplateResponse, TemplateCategoryResponse

router = APIRouter()


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available templates, optionally filtered by category."""
    service = TemplateService(db)
    
    templates = await service.get_templates(category=category)
    return templates


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get template details."""
    from sqlalchemy import select
    from app.models import Template
    
    stmt = select(Template).where(Template.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.get("/templates/categories", response_model=list[str])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all template categories."""
    service = TemplateService(db)
    
    by_category = await service.get_by_category()
    return list(by_category.keys())
