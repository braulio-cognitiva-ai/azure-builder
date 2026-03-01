"""Resource Discovery Service - Discovers existing Azure resources.

This service scans the user's Azure subscription to discover existing resources,
allowing the AI to integrate with or avoid conflicts with existing infrastructure.
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from azure.identity.aio import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource.aio import ResourceManagementClient


@dataclass
class DiscoveredResource:
    """A discovered Azure resource."""
    id: str
    name: str
    type: str
    location: str
    resource_group: str
    tags: Dict[str, str]
    sku: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    created_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "location": self.location,
            "resource_group": self.resource_group,
            "tags": self.tags,
            "sku": self.sku,
            "properties": self.properties,
            "created_time": self.created_time.isoformat() if self.created_time else None
        }


@dataclass
class ResourceInventory:
    """Complete resource inventory for a subscription."""
    subscription_id: str
    resources: List[DiscoveredResource]
    resource_groups: List[str]
    regions: List[str]
    discovered_at: datetime
    
    @property
    def resource_count(self) -> int:
        """Total resource count."""
        return len(self.resources)
    
    @property
    def resources_by_type(self) -> Dict[str, int]:
        """Count resources by type."""
        counts: Dict[str, int] = {}
        for resource in self.resources:
            counts[resource.type] = counts.get(resource.type, 0) + 1
        return counts
    
    @property
    def resources_by_region(self) -> Dict[str, int]:
        """Count resources by region."""
        counts: Dict[str, int] = {}
        for resource in self.resources:
            counts[resource.location] = counts.get(resource.location, 0) + 1
        return counts
    
    def find_similar(self, resource_type: str, name_pattern: Optional[str] = None) -> List[DiscoveredResource]:
        """Find similar resources.
        
        Args:
            resource_type: Resource type to search for
            name_pattern: Optional name pattern to match
        
        Returns:
            List of matching resources
        """
        matches = [r for r in self.resources if r.type == resource_type]
        
        if name_pattern:
            matches = [r for r in matches if name_pattern.lower() in r.name.lower()]
        
        return matches
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subscription_id": self.subscription_id,
            "resource_count": self.resource_count,
            "resources": [r.to_dict() for r in self.resources],
            "resource_groups": self.resource_groups,
            "regions": self.regions,
            "resources_by_type": self.resources_by_type,
            "resources_by_region": self.resources_by_region,
            "discovered_at": self.discovered_at.isoformat()
        }


class ResourceDiscoveryService:
    """Service for discovering existing Azure resources."""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """Initialize resource discovery service.
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Optional tenant ID for service principal auth
            client_id: Optional client ID for service principal auth
            client_secret: Optional client secret for service principal auth
        """
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
        
        self._client: Optional[ResourceManagementClient] = None
    
    async def _get_client(self) -> ResourceManagementClient:
        """Get or create resource management client."""
        if not self._client:
            self._client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._client
    
    async def discover_all(
        self,
        resource_group: Optional[str] = None,
        resource_types: Optional[List[str]] = None
    ) -> ResourceInventory:
        """Discover all resources in subscription.
        
        Args:
            resource_group: Optional specific resource group to scan
            resource_types: Optional list of resource types to filter
        
        Returns:
            ResourceInventory with discovered resources
        """
        client = await self._get_client()
        
        resources: List[DiscoveredResource] = []
        resource_groups: set = set()
        regions: set = set()
        
        try:
            # List all resources
            if resource_group:
                resource_list = client.resources.list_by_resource_group(
                    resource_group_name=resource_group
                )
            else:
                resource_list = client.resources.list()
            
            async for resource in resource_list:
                # Filter by type if specified
                if resource_types and resource.type not in resource_types:
                    continue
                
                # Extract resource group from ID
                # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/{type}/{name}
                parts = resource.id.split('/')
                rg = parts[4] if len(parts) > 4 else ""
                
                # Parse SKU if available
                sku_name = None
                if hasattr(resource, 'sku') and resource.sku:
                    sku_name = resource.sku.name
                
                discovered = DiscoveredResource(
                    id=resource.id,
                    name=resource.name,
                    type=resource.type,
                    location=resource.location or "unknown",
                    resource_group=rg,
                    tags=dict(resource.tags) if resource.tags else {},
                    sku=sku_name,
                    properties=None,  # Properties can be large, fetch separately if needed
                    created_time=resource.created_time if hasattr(resource, 'created_time') else None
                )
                
                resources.append(discovered)
                resource_groups.add(rg)
                if resource.location:
                    regions.add(resource.location)
            
        except Exception as e:
            # If discovery fails, return empty inventory with error
            print(f"Resource discovery failed: {e}")
        
        return ResourceInventory(
            subscription_id=self.subscription_id,
            resources=resources,
            resource_groups=sorted(list(resource_groups)),
            regions=sorted(list(regions)),
            discovered_at=datetime.utcnow()
        )
    
    async def check_name_conflicts(
        self,
        proposed_names: List[str],
        resource_type: Optional[str] = None
    ) -> Dict[str, bool]:
        """Check if proposed resource names conflict with existing resources.
        
        Args:
            proposed_names: List of proposed resource names
            resource_type: Optional resource type to check
        
        Returns:
            Dictionary mapping name to conflict status (True = conflict exists)
        """
        inventory = await self.discover_all(resource_types=[resource_type] if resource_type else None)
        
        existing_names = {r.name.lower() for r in inventory.resources}
        
        conflicts = {}
        for name in proposed_names:
            conflicts[name] = name.lower() in existing_names
        
        return conflicts
    
    async def get_resource_summary(self) -> Dict[str, Any]:
        """Get high-level resource summary.
        
        Returns:
            Summary dictionary with counts and statistics
        """
        inventory = await self.discover_all()
        
        return {
            "subscription_id": self.subscription_id,
            "total_resources": inventory.resource_count,
            "resource_groups": len(inventory.resource_groups),
            "regions_used": len(inventory.regions),
            "resources_by_type": inventory.resources_by_type,
            "resources_by_region": inventory.resources_by_region,
            "discovered_at": inventory.discovered_at.isoformat()
        }
    
    async def find_integration_points(
        self,
        proposed_resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find potential integration points with existing infrastructure.
        
        Args:
            proposed_resources: List of proposed resources
        
        Returns:
            List of integration suggestions
        """
        inventory = await self.discover_all()
        suggestions = []
        
        # Check for existing VNets that could be reused
        existing_vnets = inventory.find_similar("Microsoft.Network/virtualNetworks")
        if existing_vnets and any(r.get("type") == "Microsoft.Network/virtualNetworks" for r in proposed_resources):
            suggestions.append({
                "type": "integration",
                "resource_type": "VNet",
                "message": f"Found {len(existing_vnets)} existing VNet(s). Consider reusing instead of creating new.",
                "existing_resources": [v.name for v in existing_vnets]
            })
        
        # Check for existing Key Vaults
        existing_keyvaults = inventory.find_similar("Microsoft.KeyVault/vaults")
        if existing_keyvaults and any(r.get("type") == "Microsoft.KeyVault/vaults" for r in proposed_resources):
            suggestions.append({
                "type": "integration",
                "resource_type": "Key Vault",
                "message": f"Found {len(existing_keyvaults)} existing Key Vault(s). Consider reusing to centralize secrets.",
                "existing_resources": [kv.name for kv in existing_keyvaults]
            })
        
        # Check for existing Log Analytics workspaces
        existing_law = inventory.find_similar("Microsoft.OperationalInsights/workspaces")
        if existing_law:
            suggestions.append({
                "type": "integration",
                "resource_type": "Log Analytics",
                "message": f"Found {len(existing_law)} existing Log Analytics workspace(s). Consider reusing for centralized logging.",
                "existing_resources": [w.name for w in existing_law]
            })
        
        return suggestions
    
    async def close(self):
        """Close the client."""
        if self._client:
            await self._client.close()
        await self.credential.close()


async def discover_resources(
    subscription_id: str,
    resource_group: Optional[str] = None,
    credentials: Optional[Dict[str, str]] = None
) -> ResourceInventory:
    """Convenience function to discover resources.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group: Optional resource group to scan
        credentials: Optional credentials dict
    
    Returns:
        ResourceInventory
    """
    creds = credentials or {}
    discovery = ResourceDiscoveryService(
        subscription_id=subscription_id,
        tenant_id=creds.get("tenant_id"),
        client_id=creds.get("client_id"),
        client_secret=creds.get("client_secret")
    )
    
    try:
        return await discovery.discover_all(resource_group=resource_group)
    finally:
        await discovery.close()
