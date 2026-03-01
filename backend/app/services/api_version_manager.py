"""API Version Manager - Manages Azure API versions.

This service queries Azure to get the latest stable API versions for resource
providers, ensuring templates always use current APIs.
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import redis.asyncio as redis
from azure.identity.aio import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource.aio import ResourceManagementClient

from app.config import settings


@dataclass
class ApiVersion:
    """API version information."""
    resource_type: str
    version: str
    is_preview: bool
    is_default: bool
    
    @property
    def is_stable(self) -> bool:
        """Check if this is a stable (non-preview) version."""
        return not self.is_preview


class ApiVersionManager:
    """Manages API versions for Azure resource providers."""
    
    # Cache TTL: 7 days (API versions don't change frequently)
    CACHE_TTL = 7 * 24 * 60 * 60
    
    # Fallback versions (known good versions as of 2026-03)
    FALLBACK_VERSIONS = {
        "Microsoft.Compute/virtualMachines": "2023-09-01",
        "Microsoft.Network/virtualNetworks": "2023-09-01",
        "Microsoft.Network/publicIPAddresses": "2023-09-01",
        "Microsoft.Network/networkSecurityGroups": "2023-09-01",
        "Microsoft.Network/loadBalancers": "2023-09-01",
        "Microsoft.Storage/storageAccounts": "2023-01-01",
        "Microsoft.Web/sites": "2023-01-01",
        "Microsoft.Web/serverfarms": "2023-01-01",
        "Microsoft.Sql/servers": "2023-05-01-preview",
        "Microsoft.Sql/servers/databases": "2023-05-01-preview",
        "Microsoft.KeyVault/vaults": "2023-07-01",
        "Microsoft.Insights/components": "2020-02-02",
        "Microsoft.OperationalInsights/workspaces": "2022-10-01",
        "Microsoft.ContainerInstance/containerGroups": "2023-05-01",
        "Microsoft.ContainerRegistry/registries": "2023-07-01",
        "Microsoft.Cache/redis": "2023-08-01",
        "Microsoft.DBforPostgreSQL/flexibleServers": "2023-03-01-preview",
        "Microsoft.DocumentDB/databaseAccounts": "2023-11-15",
    }
    
    def __init__(
        self,
        subscription_id: str,
        redis_client: Optional[redis.Redis] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """Initialize API version manager.
        
        Args:
            subscription_id: Azure subscription ID
            redis_client: Optional Redis client for caching
            tenant_id: Optional tenant ID for service principal auth
            client_id: Optional client ID for service principal auth
            client_secret: Optional client secret for service principal auth
        """
        self.subscription_id = subscription_id
        self.redis_client = redis_client
        
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
    
    async def get_latest_version(
        self,
        resource_type: str,
        prefer_stable: bool = True
    ) -> str:
        """Get latest API version for a resource type.
        
        Args:
            resource_type: Resource type (e.g., "Microsoft.Compute/virtualMachines")
            prefer_stable: If True, prefer stable (non-preview) versions
        
        Returns:
            API version string (e.g., "2023-09-01")
        """
        # Check cache first
        cached = await self._get_cached_version(resource_type)
        if cached:
            return cached
        
        try:
            # Query Azure for versions
            versions = await self._query_versions(resource_type)
            
            if not versions:
                return self._get_fallback_version(resource_type)
            
            # Filter for stable versions if requested
            if prefer_stable:
                stable_versions = [v for v in versions if v.is_stable]
                if stable_versions:
                    versions = stable_versions
            
            # Get latest version
            latest = max(versions, key=lambda v: v.version)
            
            # Cache the result
            await self._cache_version(resource_type, latest.version)
            
            return latest.version
        
        except Exception as e:
            print(f"Failed to get API version for {resource_type}: {e}")
            return self._get_fallback_version(resource_type)
    
    async def get_versions_for_template(
        self,
        resource_types: List[str]
    ) -> Dict[str, str]:
        """Get API versions for multiple resource types.
        
        Args:
            resource_types: List of resource types
        
        Returns:
            Dictionary mapping resource type to API version
        """
        versions = {}
        
        for resource_type in resource_types:
            versions[resource_type] = await self.get_latest_version(resource_type)
        
        return versions
    
    async def _query_versions(
        self,
        resource_type: str
    ) -> List[ApiVersion]:
        """Query Azure for available API versions.
        
        Args:
            resource_type: Resource type
        
        Returns:
            List of available API versions
        """
        client = await self._get_client()
        
        # Parse resource type
        # Format: Microsoft.Compute/virtualMachines
        parts = resource_type.split('/', 1)
        if len(parts) != 2:
            return []
        
        namespace = parts[0]
        resource = parts[1]
        
        try:
            # Get provider
            provider = await client.providers.get(namespace)
            
            # Find resource type in provider
            for rt in provider.resource_types:
                if rt.resource_type.lower() == resource.lower():
                    # Convert to ApiVersion objects
                    versions = []
                    for version_str in rt.api_versions:
                        is_preview = "preview" in version_str.lower()
                        is_default = version_str == rt.default_api_version if hasattr(rt, 'default_api_version') else False
                        
                        versions.append(ApiVersion(
                            resource_type=resource_type,
                            version=version_str,
                            is_preview=is_preview,
                            is_default=is_default
                        ))
                    
                    return versions
        
        except Exception as e:
            print(f"Failed to query versions for {resource_type}: {e}")
        
        return []
    
    def _get_fallback_version(self, resource_type: str) -> str:
        """Get fallback version from known-good versions.
        
        Args:
            resource_type: Resource type
        
        Returns:
            Fallback API version
        """
        return self.FALLBACK_VERSIONS.get(resource_type, "2023-01-01")
    
    async def _get_cached_version(self, resource_type: str) -> Optional[str]:
        """Get cached API version.
        
        Args:
            resource_type: Resource type
        
        Returns:
            Cached version or None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"azure:api_version:{resource_type}"
            cached = await self.redis_client.get(cache_key)
            
            if cached:
                return cached.decode('utf-8')
        
        except Exception:
            pass
        
        return None
    
    async def _cache_version(self, resource_type: str, version: str):
        """Cache API version.
        
        Args:
            resource_type: Resource type
            version: API version to cache
        """
        if not self.redis_client:
            return
        
        try:
            cache_key = f"azure:api_version:{resource_type}"
            await self.redis_client.setex(
                cache_key,
                self.CACHE_TTL,
                version
            )
        except Exception:
            pass
    
    async def refresh_all_versions(self):
        """Refresh all API versions in cache.
        
        This should be run periodically (e.g., weekly) to keep versions up-to-date.
        """
        for resource_type in self.FALLBACK_VERSIONS.keys():
            try:
                versions = await self._query_versions(resource_type)
                if versions:
                    stable = [v for v in versions if v.is_stable]
                    if stable:
                        latest = max(stable, key=lambda v: v.version)
                        await self._cache_version(resource_type, latest.version)
            except Exception as e:
                print(f"Failed to refresh {resource_type}: {e}")
    
    async def get_version_info(self, resource_type: str) -> Dict[str, any]:
        """Get detailed version information.
        
        Args:
            resource_type: Resource type
        
        Returns:
            Dictionary with version details
        """
        versions = await self._query_versions(resource_type)
        
        stable_versions = [v for v in versions if v.is_stable]
        preview_versions = [v for v in versions if v.is_preview]
        
        return {
            "resource_type": resource_type,
            "latest_stable": max(stable_versions, key=lambda v: v.version).version if stable_versions else None,
            "latest_preview": max(preview_versions, key=lambda v: v.version).version if preview_versions else None,
            "all_versions": [v.version for v in versions],
            "stable_count": len(stable_versions),
            "preview_count": len(preview_versions),
            "fallback": self._get_fallback_version(resource_type)
        }
    
    async def close(self):
        """Close the client."""
        if self._client:
            await self._client.close()
        await self.credential.close()


# Singleton instance for easy access
_manager_instance: Optional[ApiVersionManager] = None


async def get_api_version_manager(
    subscription_id: str,
    redis_client: Optional[redis.Redis] = None
) -> ApiVersionManager:
    """Get or create API version manager instance.
    
    Args:
        subscription_id: Azure subscription ID
        redis_client: Optional Redis client
    
    Returns:
        ApiVersionManager instance
    """
    global _manager_instance
    
    if _manager_instance is None:
        _manager_instance = ApiVersionManager(
            subscription_id=subscription_id,
            redis_client=redis_client
        )
    
    return _manager_instance


async def get_latest_api_version(
    resource_type: str,
    subscription_id: str,
    prefer_stable: bool = True
) -> str:
    """Convenience function to get latest API version.
    
    Args:
        resource_type: Resource type
        subscription_id: Azure subscription ID
        prefer_stable: Prefer stable versions
    
    Returns:
        API version string
    """
    manager = await get_api_version_manager(subscription_id)
    return await manager.get_latest_version(resource_type, prefer_stable)
