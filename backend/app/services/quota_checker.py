"""Quota Checker Service - Validates Azure subscription quotas and limits.

This service checks if the user's Azure subscription has sufficient quota
to deploy the proposed architecture.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from azure.identity.aio import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.compute.aio import ComputeManagementClient
from azure.mgmt.network.aio import NetworkManagementClient
from azure.mgmt.storage.aio import StorageManagementClient

from app.schemas.proposal import ResourceDefinition


class QuotaStatus(str, Enum):
    """Quota check status."""
    OK = "ok"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    UNKNOWN = "unknown"


@dataclass
class QuotaCheck:
    """Result of a quota check."""
    resource_type: str
    quota_name: str
    current_usage: int
    quota_limit: int
    requested: int
    status: QuotaStatus
    message: str
    
    @property
    def available(self) -> int:
        """Calculate available quota."""
        return self.quota_limit - self.current_usage
    
    @property
    def after_deployment(self) -> int:
        """Calculate usage after deployment."""
        return self.current_usage + self.requested


@dataclass
class QuotaReport:
    """Complete quota validation report."""
    subscription_id: str
    region: str
    checks: List[QuotaCheck]
    overall_status: QuotaStatus
    can_deploy: bool
    warnings: List[str]
    errors: List[str]
    
    @property
    def has_warnings(self) -> bool:
        """Check if any warnings exist."""
        return len(self.warnings) > 0 or any(c.status == QuotaStatus.WARNING for c in self.checks)
    
    @property
    def has_errors(self) -> bool:
        """Check if any errors exist."""
        return len(self.errors) > 0 or any(c.status == QuotaStatus.EXCEEDED for c in self.checks)


class QuotaCheckerService:
    """Service for checking Azure subscription quotas."""
    
    # Resource type to quota mapping
    QUOTA_MAPPINGS = {
        # Compute
        "Microsoft.Compute/virtualMachines": {
            "quota_category": "compute",
            "metrics": ["cores", "vms"]
        },
        "Microsoft.Web/sites": {
            "quota_category": "app_service",
            "metrics": ["sites"]
        },
        "Microsoft.ContainerInstance/containerGroups": {
            "quota_category": "container_instance",
            "metrics": ["container_groups"]
        },
        
        # Networking
        "Microsoft.Network/publicIPAddresses": {
            "quota_category": "network",
            "metrics": ["public_ips"]
        },
        "Microsoft.Network/loadBalancers": {
            "quota_category": "network",
            "metrics": ["load_balancers"]
        },
        "Microsoft.Network/virtualNetworks": {
            "quota_category": "network",
            "metrics": ["virtual_networks"]
        },
        
        # Storage
        "Microsoft.Storage/storageAccounts": {
            "quota_category": "storage",
            "metrics": ["storage_accounts"]
        },
    }
    
    # SKU to vCPU mapping (simplified)
    SKU_VCPU_MAP = {
        # VMs
        "Standard_B1s": 1,
        "Standard_B1ms": 1,
        "Standard_B2s": 2,
        "Standard_B2ms": 2,
        "Standard_B4ms": 4,
        "Standard_D2s_v3": 2,
        "Standard_D4s_v3": 4,
        "Standard_D8s_v3": 8,
        
        # App Service Plans
        "B1": 1,
        "B2": 2,
        "B3": 4,
        "S1": 1,
        "S2": 2,
        "S3": 4,
        "P1V2": 1,
        "P2V2": 2,
        "P3V2": 4,
        "P1V3": 2,
        "P2V3": 4,
        "P3V3": 8,
    }
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """Initialize quota checker.
        
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
            # Use default credential chain (managed identity, CLI, etc.)
            self.credential = DefaultAzureCredential()
        
        # Initialize clients (will be created lazily)
        self._compute_client: Optional[ComputeManagementClient] = None
        self._network_client: Optional[NetworkManagementClient] = None
        self._storage_client: Optional[StorageManagementClient] = None
    
    async def _get_compute_client(self) -> ComputeManagementClient:
        """Get or create compute client."""
        if not self._compute_client:
            self._compute_client = ComputeManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._compute_client
    
    async def _get_network_client(self) -> NetworkManagementClient:
        """Get or create network client."""
        if not self._network_client:
            self._network_client = NetworkManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._network_client
    
    async def _get_storage_client(self) -> StorageManagementClient:
        """Get or create storage client."""
        if not self._storage_client:
            self._storage_client = StorageManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._storage_client
    
    async def check_quotas(
        self,
        resources: List[ResourceDefinition],
        region: str = "eastus"
    ) -> QuotaReport:
        """Check if subscription has sufficient quota for resources.
        
        Args:
            resources: List of resources to deploy
            region: Azure region (location)
        
        Returns:
            QuotaReport with detailed quota information
        """
        checks: List[QuotaCheck] = []
        warnings: List[str] = []
        errors: List[str] = []
        
        # Aggregate resource requirements
        requirements = self._aggregate_requirements(resources)
        
        try:
            # Check compute quotas (vCPUs, VMs)
            if requirements["vcpus"] > 0 or requirements["vms"] > 0:
                compute_checks = await self._check_compute_quota(
                    region=region,
                    vcpus_needed=requirements["vcpus"],
                    vms_needed=requirements["vms"]
                )
                checks.extend(compute_checks)
            
            # Check network quotas
            if requirements["public_ips"] > 0:
                network_checks = await self._check_network_quota(
                    region=region,
                    public_ips_needed=requirements["public_ips"],
                    vnets_needed=requirements["vnets"]
                )
                checks.extend(network_checks)
            
            # Check storage quotas
            if requirements["storage_accounts"] > 0:
                storage_checks = await self._check_storage_quota(
                    region=region,
                    accounts_needed=requirements["storage_accounts"]
                )
                checks.extend(storage_checks)
            
        except Exception as e:
            # If quota check fails, warn but don't block
            warnings.append(f"Unable to verify quotas: {str(e)}")
        
        # Analyze results
        for check in checks:
            if check.status == QuotaStatus.EXCEEDED:
                errors.append(
                    f"{check.quota_name}: Need {check.requested}, but only {check.available} available "
                    f"({check.current_usage}/{check.quota_limit} used)"
                )
            elif check.status == QuotaStatus.WARNING:
                warnings.append(
                    f"{check.quota_name}: After deployment, {check.after_deployment}/{check.quota_limit} used "
                    f"({int((check.after_deployment / check.quota_limit) * 100)}%)"
                )
        
        # Determine overall status
        if any(c.status == QuotaStatus.EXCEEDED for c in checks):
            overall_status = QuotaStatus.EXCEEDED
            can_deploy = False
        elif any(c.status == QuotaStatus.WARNING for c in checks):
            overall_status = QuotaStatus.WARNING
            can_deploy = True
        else:
            overall_status = QuotaStatus.OK
            can_deploy = True
        
        return QuotaReport(
            subscription_id=self.subscription_id,
            region=region,
            checks=checks,
            overall_status=overall_status,
            can_deploy=can_deploy,
            warnings=warnings,
            errors=errors
        )
    
    def _aggregate_requirements(self, resources: List[ResourceDefinition]) -> Dict[str, int]:
        """Aggregate resource requirements from proposal.
        
        Args:
            resources: List of resources
        
        Returns:
            Dictionary with aggregated counts
        """
        requirements = {
            "vcpus": 0,
            "vms": 0,
            "public_ips": 0,
            "vnets": 0,
            "storage_accounts": 0,
            "app_services": 0,
        }
        
        for resource in resources:
            resource_type = resource.type
            sku = resource.sku
            
            # Count VMs and vCPUs
            if resource_type == "Microsoft.Compute/virtualMachines":
                requirements["vms"] += 1
                requirements["vcpus"] += self.SKU_VCPU_MAP.get(sku, 2)  # Default 2 vCPUs
            
            # Count App Services
            elif resource_type in ["Microsoft.Web/sites", "Microsoft.Web/serverFarms"]:
                requirements["app_services"] += 1
                # App Service Plans also consume vCPU-like quota
                requirements["vcpus"] += self.SKU_VCPU_MAP.get(sku, 1)
            
            # Count Container Instances
            elif resource_type == "Microsoft.ContainerInstance/containerGroups":
                props = resource.properties or {}
                cpu = props.get("cpu", 1)
                requirements["vcpus"] += int(cpu)
            
            # Count network resources
            elif resource_type == "Microsoft.Network/publicIPAddresses":
                requirements["public_ips"] += 1
            elif resource_type == "Microsoft.Network/virtualNetworks":
                requirements["vnets"] += 1
            
            # Count storage accounts
            elif resource_type == "Microsoft.Storage/storageAccounts":
                requirements["storage_accounts"] += 1
        
        return requirements
    
    async def _check_compute_quota(
        self,
        region: str,
        vcpus_needed: int,
        vms_needed: int
    ) -> List[QuotaCheck]:
        """Check compute quotas (vCPUs, VMs)."""
        checks = []
        
        try:
            client = await self._get_compute_client()
            
            # Get usage for the region
            usages = client.usage.list(location=region)
            
            async for usage in usages:
                # Check vCPU quota
                if "cores" in usage.name.value.lower() and "total" in usage.name.value.lower():
                    checks.append(QuotaCheck(
                        resource_type="Compute",
                        quota_name="Total Regional vCPUs",
                        current_usage=usage.current_value,
                        quota_limit=usage.limit,
                        requested=vcpus_needed,
                        status=self._determine_status(
                            current=usage.current_value,
                            limit=usage.limit,
                            requested=vcpus_needed
                        ),
                        message=f"Requesting {vcpus_needed} vCPUs"
                    ))
                
                # Check VM quota
                elif "virtualmachines" in usage.name.value.lower():
                    checks.append(QuotaCheck(
                        resource_type="Compute",
                        quota_name="Virtual Machines",
                        current_usage=usage.current_value,
                        quota_limit=usage.limit,
                        requested=vms_needed,
                        status=self._determine_status(
                            current=usage.current_value,
                            limit=usage.limit,
                            requested=vms_needed
                        ),
                        message=f"Requesting {vms_needed} VMs"
                    ))
        
        except Exception as e:
            # Return unknown status if check fails
            checks.append(QuotaCheck(
                resource_type="Compute",
                quota_name="vCPU Quota",
                current_usage=0,
                quota_limit=0,
                requested=vcpus_needed,
                status=QuotaStatus.UNKNOWN,
                message=f"Unable to check quota: {str(e)}"
            ))
        
        return checks
    
    async def _check_network_quota(
        self,
        region: str,
        public_ips_needed: int,
        vnets_needed: int
    ) -> List[QuotaCheck]:
        """Check network quotas."""
        checks = []
        
        try:
            client = await self._get_network_client()
            
            # Get usage for the region
            usages = client.usages.list(location=region)
            
            async for usage in usages:
                # Check public IP quota
                if "publicipaddresses" in usage.name.value.lower():
                    checks.append(QuotaCheck(
                        resource_type="Network",
                        quota_name="Public IP Addresses",
                        current_usage=usage.current_value,
                        quota_limit=usage.limit,
                        requested=public_ips_needed,
                        status=self._determine_status(
                            current=usage.current_value,
                            limit=usage.limit,
                            requested=public_ips_needed
                        ),
                        message=f"Requesting {public_ips_needed} public IPs"
                    ))
                
                # Check VNet quota
                elif "virtualnetworks" in usage.name.value.lower():
                    checks.append(QuotaCheck(
                        resource_type="Network",
                        quota_name="Virtual Networks",
                        current_usage=usage.current_value,
                        quota_limit=usage.limit,
                        requested=vnets_needed,
                        status=self._determine_status(
                            current=usage.current_value,
                            limit=usage.limit,
                            requested=vnets_needed
                        ),
                        message=f"Requesting {vnets_needed} VNets"
                    ))
        
        except Exception as e:
            checks.append(QuotaCheck(
                resource_type="Network",
                quota_name="Network Resources",
                current_usage=0,
                quota_limit=0,
                requested=public_ips_needed + vnets_needed,
                status=QuotaStatus.UNKNOWN,
                message=f"Unable to check quota: {str(e)}"
            ))
        
        return checks
    
    async def _check_storage_quota(
        self,
        region: str,
        accounts_needed: int
    ) -> List[QuotaCheck]:
        """Check storage account quotas."""
        checks = []
        
        try:
            client = await self._get_storage_client()
            
            # Get usage for the subscription (storage is subscription-wide, not regional)
            usages = client.usages.list_by_location(location=region)
            
            async for usage in usages:
                if "storageaccounts" in usage.name.value.lower():
                    checks.append(QuotaCheck(
                        resource_type="Storage",
                        quota_name="Storage Accounts",
                        current_usage=usage.current_value,
                        quota_limit=usage.limit,
                        requested=accounts_needed,
                        status=self._determine_status(
                            current=usage.current_value,
                            limit=usage.limit,
                            requested=accounts_needed
                        ),
                        message=f"Requesting {accounts_needed} storage accounts"
                    ))
        
        except Exception as e:
            checks.append(QuotaCheck(
                resource_type="Storage",
                quota_name="Storage Accounts",
                current_usage=0,
                quota_limit=0,
                requested=accounts_needed,
                status=QuotaStatus.UNKNOWN,
                message=f"Unable to check quota: {str(e)}"
            ))
        
        return checks
    
    def _determine_status(self, current: int, limit: int, requested: int) -> QuotaStatus:
        """Determine quota status.
        
        Args:
            current: Current usage
            limit: Quota limit
            requested: Requested additional quota
        
        Returns:
            QuotaStatus
        """
        available = limit - current
        after_deployment = current + requested
        
        # Exceeded if not enough available
        if requested > available:
            return QuotaStatus.EXCEEDED
        
        # Warning if usage will be >80% after deployment
        if after_deployment / limit > 0.8:
            return QuotaStatus.WARNING
        
        return QuotaStatus.OK
    
    async def close(self):
        """Close all clients."""
        if self._compute_client:
            await self._compute_client.close()
        if self._network_client:
            await self._network_client.close()
        if self._storage_client:
            await self._storage_client.close()
        await self.credential.close()


async def check_quotas(
    subscription_id: str,
    resources: List[ResourceDefinition],
    region: str = "eastus",
    credentials: Optional[Dict[str, str]] = None
) -> QuotaReport:
    """Convenience function to check quotas.
    
    Args:
        subscription_id: Azure subscription ID
        resources: Resources to check
        region: Azure region
        credentials: Optional credentials dict with tenant_id, client_id, client_secret
    
    Returns:
        QuotaReport
    """
    creds = credentials or {}
    checker = QuotaCheckerService(
        subscription_id=subscription_id,
        tenant_id=creds.get("tenant_id"),
        client_id=creds.get("client_id"),
        client_secret=creds.get("client_secret")
    )
    
    try:
        report = await checker.check_quotas(resources, region)
        return report
    finally:
        await checker.close()
