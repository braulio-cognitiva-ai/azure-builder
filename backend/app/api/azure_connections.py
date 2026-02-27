"""Azure Connections API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User, AzureConnection, ConnectionStatus
from app.services import AzureConnectionService
from app.schemas.azure_connection import (
    AzureConnectionCreate,
    AzureConnectionResponse,
    SubscriptionQuotasResponse,
    ExistingResourcesResponse
)

router = APIRouter()


@router.post("/azure/connect", response_model=AzureConnectionResponse, status_code=status.HTTP_201_CREATED)
async def connect_azure_subscription(
    data: AzureConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Connect an Azure subscription."""
    service = AzureConnectionService(db)
    
    # Validate credentials
    is_valid = await service.validate_connection(
        subscription_id=data.subscription_id,
        azure_tenant_id=data.azure_tenant_id,
        client_id=data.client_id,
        client_secret=data.client_secret
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Azure credentials"
        )
    
    # Create connection
    connection = AzureConnection(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        subscription_id=data.subscription_id,
        azure_tenant_id=data.azure_tenant_id,
        subscription_name=data.subscription_name,
        auth_method=data.auth_method,
        status=ConnectionStatus.ACTIVE
    )
    
    # Store credentials in Key Vault
    key_vault_ref = await service.store_credentials_in_keyvault(
        connection_id=connection.id,
        credentials={
            "client_id": data.client_id,
            "client_secret": data.client_secret,
            "tenant_id": data.azure_tenant_id,
            "subscription_id": data.subscription_id
        }
    )
    
    connection.key_vault_ref = key_vault_ref
    
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    
    return connection


@router.get("/azure/status", response_model=list[AzureConnectionResponse])
async def get_azure_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all Azure connections for tenant."""
    stmt = select(AzureConnection).where(
        AzureConnection.tenant_id == current_user.tenant_id
    )
    
    result = await db.execute(stmt)
    connections = result.scalars().all()
    
    return list(connections)


@router.get("/azure/{connection_id}/quotas", response_model=SubscriptionQuotasResponse)
async def get_subscription_quotas(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Azure subscription quotas and usage."""
    service = AzureConnectionService(db)
    
    quotas = await service.get_subscription_quotas(connection_id)
    
    return {
        "subscription_id": str(connection_id),
        "quotas": [],  # TODO: Parse quotas into QuotaInfo objects
        "last_checked": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
    }


@router.get("/azure/{connection_id}/resources", response_model=ExistingResourcesResponse)
async def get_existing_resources(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get existing resources in Azure subscription."""
    service = AzureConnectionService(db)
    
    resources = await service.get_existing_resources(connection_id)
    
    return {
        "subscription_id": str(connection_id),
        "total_resources": len(resources),
        "resources": resources,
        "resource_groups": []
    }


@router.delete("/azure/{connection_id}")
async def delete_azure_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove Azure connection."""
    stmt = select(AzureConnection).where(
        AzureConnection.id == connection_id,
        AzureConnection.tenant_id == current_user.tenant_id
    )
    
    result = await db.execute(stmt)
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    await db.delete(connection)
    await db.commit()
    
    return {"status": "deleted"}
