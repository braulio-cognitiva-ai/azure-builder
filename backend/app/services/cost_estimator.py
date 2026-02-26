"""Cost estimation service."""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourceCost:
    """Cost estimate for a single resource."""

    resource_name: str
    resource_type: str
    region: str
    sku: str
    hourly_cost: float
    monthly_cost: float
    currency: str = "USD"


@dataclass
class CostEstimate:
    """Complete cost estimate for an execution."""

    resources: list[ResourceCost]
    total_monthly_cost: float
    currency: str = "USD"


class CostEstimator:
    """Service for estimating Azure resource costs."""

    # Simplified cost database (in production, query Azure Pricing API)
    COST_DATABASE = {
        # Virtual Machines
        "vm_standard_b1s": {"hourly": 0.0104, "monthly": 7.59},
        "vm_standard_b2s": {"hourly": 0.0416, "monthly": 30.37},
        "vm_standard_d2s_v3": {"hourly": 0.096, "monthly": 70.08},
        
        # App Service Plans
        "plan_b1": {"hourly": 0.075, "monthly": 54.75},
        "plan_p1v2": {"hourly": 0.147, "monthly": 107.28},
        
        # SQL Database
        "sql_s0": {"hourly": 0.0206, "monthly": 15.0},
        "sql_s1": {"hourly": 0.0411, "monthly": 30.0},
        
        # Storage Account
        "storage_standard": {"hourly": 0.003, "monthly": 2.0},
    }

    async def estimate_from_commands(self, commands: list[str]) -> CostEstimate:
        """
        Estimate costs from Azure CLI commands.
        
        Args:
            commands: List of Azure CLI commands
            
        Returns:
            Cost estimate
        """
        resources = []

        for command in commands:
            # Parse resource type and SKU from command
            resource_cost = self._parse_command_cost(command)
            if resource_cost:
                resources.append(resource_cost)

        total_monthly = sum(r.monthly_cost for r in resources)

        return CostEstimate(
            resources=resources,
            total_monthly_cost=total_monthly,
            currency="USD",
        )

    def _parse_command_cost(self, command: str) -> Optional[ResourceCost]:
        """
        Parse command to estimate cost.
        
        Args:
            command: Azure CLI command
            
        Returns:
            Resource cost or None if unable to estimate
        """
        # Extract resource type
        if "az vm create" in command:
            return self._estimate_vm_cost(command)
        elif "az appservice plan create" in command:
            return self._estimate_app_service_cost(command)
        elif "az sql db create" in command:
            return self._estimate_sql_cost(command)
        elif "az storage account create" in command:
            return self._estimate_storage_cost(command)
        
        return None

    def _estimate_vm_cost(self, command: str) -> Optional[ResourceCost]:
        """Estimate VM cost from create command."""
        # Extract VM size
        size_match = re.search(r"--size\s+([^\s]+)", command)
        name_match = re.search(r"--name\s+([^\s]+)", command)
        location_match = re.search(r"--location\s+([^\s]+)", command)

        if not size_match:
            return None

        size = size_match.group(1).lower().replace("_", "_")
        key = f"vm_{size}"
        cost = self.COST_DATABASE.get(key, {"hourly": 0.1, "monthly": 73.0})

        return ResourceCost(
            resource_name=name_match.group(1) if name_match else "vm",
            resource_type="Virtual Machine",
            region=location_match.group(1) if location_match else "eastus",
            sku=size,
            hourly_cost=cost["hourly"],
            monthly_cost=cost["monthly"],
        )

    def _estimate_app_service_cost(self, command: str) -> Optional[ResourceCost]:
        """Estimate App Service Plan cost."""
        sku_match = re.search(r"--sku\s+([^\s]+)", command)
        name_match = re.search(r"--name\s+([^\s]+)", command)

        if not sku_match:
            return None

        sku = sku_match.group(1).lower()
        key = f"plan_{sku}"
        cost = self.COST_DATABASE.get(key, {"hourly": 0.075, "monthly": 54.75})

        return ResourceCost(
            resource_name=name_match.group(1) if name_match else "app-plan",
            resource_type="App Service Plan",
            region="eastus",
            sku=sku,
            hourly_cost=cost["hourly"],
            monthly_cost=cost["monthly"],
        )

    def _estimate_sql_cost(self, command: str) -> Optional[ResourceCost]:
        """Estimate SQL Database cost."""
        sku_match = re.search(r"--service-objective\s+([^\s]+)", command)
        name_match = re.search(r"--name\s+([^\s]+)", command)

        if not sku_match:
            return None

        sku = sku_match.group(1).lower()
        key = f"sql_{sku}"
        cost = self.COST_DATABASE.get(key, {"hourly": 0.0206, "monthly": 15.0})

        return ResourceCost(
            resource_name=name_match.group(1) if name_match else "sql-db",
            resource_type="SQL Database",
            region="eastus",
            sku=sku,
            hourly_cost=cost["hourly"],
            monthly_cost=cost["monthly"],
        )

    def _estimate_storage_cost(self, command: str) -> Optional[ResourceCost]:
        """Estimate Storage Account cost."""
        name_match = re.search(r"--name\s+([^\s]+)", command)

        return ResourceCost(
            resource_name=name_match.group(1) if name_match else "storage",
            resource_type="Storage Account",
            region="eastus",
            sku="Standard_LRS",
            hourly_cost=0.003,
            monthly_cost=2.0,
        )
