"""Audit API routes."""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User, AuditLog
from app.services import AuditService

router = APIRouter()


@router.get("/audit", response_model=list)
async def query_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Query audit logs with filters."""
    filters = {}
    
    if action:
        filters["action"] = action
    if entity_type:
        filters["entity_type"] = entity_type
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    
    logs = await AuditService.get_recent_logs(
        db=db,
        tenant_id=current_user.tenant_id,
        limit=limit
    )
    
    return logs
