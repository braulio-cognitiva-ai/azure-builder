"""Pricing API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services import PricingService

router = APIRouter()


class ResourceEstimate(BaseModel):
    """Resource for cost estimation."""
    type: str
    sku: str
    region: str
    name: str


class EstimateRequest(BaseModel):
    """Request for cost estimation."""
    resources: List[ResourceEstimate]


class CompareRegionsRequest(BaseModel):
    """Request for region comparison."""
    resources: List[ResourceEstimate]
    regions: List[str]


class CompareSkusRequest(BaseModel):
    """Request for SKU comparison."""
    service: str
    skus: List[str]
    region: str


@router.post("/pricing/estimate")
async def estimate_cost(
    data: EstimateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Estimate cost for a set of resources."""
    service = PricingService(db)
    
    resources = [r.dict() for r in data.resources]
    estimate = await service.estimate_monthly_cost(resources)
    
    return estimate


@router.post("/pricing/compare-regions")
async def compare_regions(
    data: CompareRegionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare cost across multiple regions."""
    service = PricingService(db)
    
    resources = [r.dict() for r in data.resources]
    comparison = await service.compare_regions(resources, data.regions)
    
    return comparison


@router.post("/pricing/compare-skus")
async def compare_skus(
    data: CompareSkusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare cost across multiple SKUs."""
    service = PricingService(db)
    
    comparison = await service.compare_skus(
        service=data.service,
        skus=data.skus,
        region=data.region
    )
    
    return comparison
