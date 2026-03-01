"""Resource Tracker Service - Tracks deployed Azure resources.

This service syncs deployed resources with Azure, monitors costs, and detects drift.
"""
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from azure.identity.aio import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource.aio import ResourceManagementClient
from azure.mgmt.costmanagement.aio import CostManagementClient

from app.models.deployed_resource import DeployedResource, ResourceStatus
from app.models.deployment import DeploymentRequest


class ResourceTrackerService:
    """Service for tracking deployed Azure resources."""
    
    def __init__(
        self,
        session: AsyncSession,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """Initialize resource tracker.
        
        Args:
            session: Database session
            subscription_id: Azure subscription ID
            tenant_id: Optional tenant ID for service principal
            client_id: Optional client ID for service principal
            client_secret: Optional client secret for service principal
        """
        self.session = session
        self.subscription_id = subscription_id
        
        # Initialize credential
        if tenant_id and client_id and client_secret:
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            self.credential = DefaultAzureCredential()
        
        self._resource_client: Optional[ResourceManagementClient] = None
        self._cost_client: Optional[CostManagementClient] = None
    
    async def _get_resource_client(self) -> ResourceManagementClient:
        """Get or create resource management client."""
        if not self._resource_client:
            self._resource_client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._resource_client
    
    async def _get_cost_client(self) -> CostManagementClient:
        """Get or create cost management client."""
        if not self._cost_client:
            self._cost_client = CostManagementClient(
                credential=self.credential
            )
        return self._cost_client
    
    async def track_deployment(
        self,
        deployment: DeploymentRequest,
        resource_ids: List[str]
    ) -> List[DeployedResource]:
        """Track resources from a deployment.
        
        Args:
            deployment: Deployment request
            resource_ids: List of Azure resource IDs
        
        Returns:
            List of tracked resources
        """
        client = await self._get_resource_client()
        tracked_resources = []
        
        for resource_id in resource_ids:
            try:
                # Get resource details from Azure
                # Parse resource ID: /subscriptions/{sub}/resourceGroups/{rg}/providers/{type}/{name}
                parts = resource_id.split('/')
                if len(parts) < 9:
                    continue
                
                resource_group = parts[4]
                resource_type = f"{parts[6]}/{parts[7]}"
                resource_name = parts[8]
                
                # Get resource from Azure
                resource = await client.resources.get_by_id(
                    resource_id=resource_id,
                    api_version="2021-04-01"
                )
                
                # Extract SKU if available
                sku_name = None
                if hasattr(resource, 'sku') and resource.sku:
                    sku_name = resource.sku.name
                
                # Create tracked resource
                deployed_resource = DeployedResource(
                    id=uuid.uuid4(),
                    deployment_id=deployment.id,
                    tenant_id=deployment.tenant_id,
                    project_id=deployment.proposal.project_id,
                    azure_resource_id=resource_id,
                    resource_type=resource_type,
                    name=resource_name,
                    resource_group=resource_group,
                    region=resource.location or "unknown",
                    sku=sku_name,
                    status=ResourceStatus.ACTIVE,
                    properties=dict(resource.properties) if resource.properties else {},
                    tags=dict(resource.tags) if resource.tags else {},
                    expected_config={"properties": dict(resource.properties) if resource.properties else {}},
                    actual_config={"properties": dict(resource.properties) if resource.properties else {}},
                    deployed_at=datetime.utcnow(),
                    last_synced_at=datetime.utcnow()
                )
                
                self.session.add(deployed_resource)
                tracked_resources.append(deployed_resource)
                
            except Exception as e:
                print(f"Failed to track resource {resource_id}: {e}")
                continue
        
        await self.session.commit()
        return tracked_resources
    
    async def sync_resource(
        self,
        deployed_resource: DeployedResource
    ) -> DeployedResource:
        """Sync a deployed resource with Azure.
        
        Args:
            deployed_resource: Deployed resource to sync
        
        Returns:
            Updated deployed resource
        """
        client = await self._get_resource_client()
        
        try:
            # Get resource from Azure
            resource = await client.resources.get_by_id(
                resource_id=deployed_resource.azure_resource_id,
                api_version="2021-04-01"
            )
            
            # Update actual config
            deployed_resource.actual_config = {
                "properties": dict(resource.properties) if resource.properties else {}
            }
            
            # Update tags
            deployed_resource.tags = dict(resource.tags) if resource.tags else {}
            
            # Update SKU if available
            if hasattr(resource, 'sku') and resource.sku:
                deployed_resource.sku = resource.sku.name
            
            # Detect drift
            deployed_resource.has_drift = self._detect_drift(
                deployed_resource.expected_config,
                deployed_resource.actual_config
            )
            
            if deployed_resource.has_drift and not deployed_resource.drift_detected_at:
                deployed_resource.drift_detected_at = datetime.utcnow()
            elif not deployed_resource.has_drift:
                deployed_resource.drift_detected_at = None
            
            deployed_resource.status = ResourceStatus.ACTIVE
            deployed_resource.last_synced_at = datetime.utcnow()
            
        except Exception as e:
            # Resource might be deleted
            if "NotFound" in str(e) or "ResourceNotFound" in str(e):
                deployed_resource.status = ResourceStatus.DELETED
                deployed_resource.deleted_at = datetime.utcnow()
            else:
                deployed_resource.status = ResourceStatus.UNKNOWN
            
            deployed_resource.last_synced_at = datetime.utcnow()
        
        await self.session.commit()
        return deployed_resource
    
    async def sync_project_resources(
        self,
        project_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[DeployedResource]:
        """Sync all resources for a project.
        
        Args:
            project_id: Project ID
            tenant_id: Tenant ID
        
        Returns:
            List of synced resources
        """
        # Get all active resources for project
        result = await self.session.execute(
            select(DeployedResource).where(
                and_(
                    DeployedResource.project_id == project_id,
                    DeployedResource.tenant_id == tenant_id,
                    DeployedResource.status == ResourceStatus.ACTIVE
                )
            )
        )
        resources = result.scalars().all()
        
        synced = []
        for resource in resources:
            synced_resource = await self.sync_resource(resource)
            synced.append(synced_resource)
        
        return synced
    
    async def update_costs(
        self,
        deployed_resource: DeployedResource
    ) -> DeployedResource:
        """Update cost information for a resource.
        
        Args:
            deployed_resource: Deployed resource
        
        Returns:
            Updated resource with cost info
        """
        try:
            cost_client = await self._get_cost_client()
            
            # Get costs for current month
            now = datetime.utcnow()
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            
            # Build scope
            scope = f"/subscriptions/{self.subscription_id}"
            
            # Query cost data
            # Note: This is a simplified example. The actual Cost Management API
            # requires more complex query parameters
            query = {
                "type": "Usage",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat()
                },
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {
                        "totalCost": {
                            "name": "PreTaxCost",
                            "function": "Sum"
                        }
                    },
                    "filter": {
                        "dimensions": {
                            "name": "ResourceId",
                            "operator": "In",
                            "values": [deployed_resource.azure_resource_id]
                        }
                    }
                }
            }
            
            # Execute query
            result = await cost_client.query.usage(scope=scope, parameters=query)
            
            # Parse result
            total_cost = Decimal("0.00")
            if result.rows:
                for row in result.rows:
                    # Row format: [cost, date, resourceId, ...]
                    if row and len(row) > 0:
                        total_cost += Decimal(str(row[0]))
            
            deployed_resource.actual_cost_mtd = total_cost
            deployed_resource.last_cost_update = datetime.utcnow()
            
        except Exception as e:
            print(f"Failed to update costs for {deployed_resource.name}: {e}")
        
        await self.session.commit()
        return deployed_resource
    
    async def update_all_costs(
        self,
        project_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[DeployedResource]:
        """Update costs for all resources in a project.
        
        Args:
            project_id: Project ID
            tenant_id: Tenant ID
        
        Returns:
            List of updated resources
        """
        # Get all active resources
        result = await self.session.execute(
            select(DeployedResource).where(
                and_(
                    DeployedResource.project_id == project_id,
                    DeployedResource.tenant_id == tenant_id,
                    DeployedResource.status == ResourceStatus.ACTIVE
                )
            )
        )
        resources = result.scalars().all()
        
        updated = []
        for resource in resources:
            updated_resource = await self.update_costs(resource)
            updated.append(updated_resource)
        
        return updated
    
    def _detect_drift(
        self,
        expected: Optional[Dict[str, Any]],
        actual: Optional[Dict[str, Any]]
    ) -> bool:
        """Detect if configuration has drifted.
        
        Args:
            expected: Expected configuration
            actual: Actual configuration
        
        Returns:
            True if drift detected
        """
        if not expected or not actual:
            return False
        
        # Compare important properties
        # This is a simplified comparison - in production you'd want more sophisticated logic
        expected_props = expected.get("properties", {})
        actual_props = actual.get("properties", {})
        
        # Check for differences in key properties
        # (Ignore certain fields that naturally change, like provisioningState)
        ignore_keys = {"provisioningState", "createdTime", "changedTime"}
        
        for key in expected_props:
            if key in ignore_keys:
                continue
            
            if key not in actual_props:
                return True  # Property removed
            
            if expected_props[key] != actual_props[key]:
                return True  # Property changed
        
        # Check for new properties
        for key in actual_props:
            if key in ignore_keys:
                continue
            
            if key not in expected_props:
                return True  # New property added
        
        return False
    
    async def get_project_summary(
        self,
        project_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get summary of deployed resources for a project.
        
        Args:
            project_id: Project ID
            tenant_id: Tenant ID
        
        Returns:
            Summary dictionary
        """
        result = await self.session.execute(
            select(DeployedResource).where(
                and_(
                    DeployedResource.project_id == project_id,
                    DeployedResource.tenant_id == tenant_id
                )
            )
        )
        resources = result.scalars().all()
        
        active_count = sum(1 for r in resources if r.status == ResourceStatus.ACTIVE)
        deleted_count = sum(1 for r in resources if r.status == ResourceStatus.DELETED)
        drift_count = sum(1 for r in resources if r.has_drift)
        
        total_estimated_cost = sum(
            r.monthly_cost_estimate for r in resources 
            if r.status == ResourceStatus.ACTIVE and r.monthly_cost_estimate
        ) or Decimal("0.00")
        
        total_actual_cost = sum(
            r.actual_cost_mtd for r in resources 
            if r.status == ResourceStatus.ACTIVE and r.actual_cost_mtd
        ) or Decimal("0.00")
        
        # Group by type
        by_type = {}
        for resource in resources:
            if resource.status != ResourceStatus.ACTIVE:
                continue
            
            if resource.resource_type not in by_type:
                by_type[resource.resource_type] = {
                    "count": 0,
                    "estimated_cost": Decimal("0.00"),
                    "actual_cost": Decimal("0.00")
                }
            
            by_type[resource.resource_type]["count"] += 1
            if resource.monthly_cost_estimate:
                by_type[resource.resource_type]["estimated_cost"] += resource.monthly_cost_estimate
            if resource.actual_cost_mtd:
                by_type[resource.resource_type]["actual_cost"] += resource.actual_cost_mtd
        
        return {
            "total_resources": len(resources),
            "active": active_count,
            "deleted": deleted_count,
            "has_drift": drift_count,
            "estimated_monthly_cost": float(total_estimated_cost),
            "actual_cost_mtd": float(total_actual_cost),
            "by_type": {
                k: {
                    "count": v["count"],
                    "estimated_cost": float(v["estimated_cost"]),
                    "actual_cost": float(v["actual_cost"])
                }
                for k, v in by_type.items()
            }
        }
    
    async def close(self):
        """Close clients."""
        if self._resource_client:
            await self._resource_client.close()
        if self._cost_client:
            await self._cost_client.close()
        await self.credential.close()
