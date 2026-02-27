"""Deployment Service - Handles deployment lifecycle and state machine."""
import uuid
import json
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import (
    DeploymentRequest,
    DeploymentStatus,
    DeploymentResource,
    ResourceStatus,
    ExecutionLog,
    LogLevel,
    ArchitectureProposal,
    ProposalOption
)


class DeploymentService:
    """Service for managing deployments."""
    
    def __init__(self, session: AsyncSession):
        """Initialize deployment service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def create_deployment(
        self,
        proposal_id: uuid.UUID,
        selected_option_number: int,
        created_by: uuid.UUID,
        parameters: Optional[dict] = None
    ) -> DeploymentRequest:
        """Create deployment from selected proposal option.
        
        Args:
            proposal_id: Proposal ID
            selected_option_number: Selected option number
            created_by: User ID creating the deployment
            parameters: Optional deployment parameters
        
        Returns:
            Created deployment
        """
        # Get proposal and option
        stmt = select(ArchitectureProposal).where(
            ArchitectureProposal.id == proposal_id
        ).options(
            selectinload(ArchitectureProposal.options)
        )
        result = await self.session.execute(stmt)
        proposal = result.scalar_one()
        
        # Get selected option
        selected_option = next(
            (opt for opt in proposal.options if opt.option_number == selected_option_number),
            None
        )
        
        if not selected_option:
            raise ValueError(f"Option {selected_option_number} not found")
        
        # Create deployment
        deployment = DeploymentRequest(
            id=uuid.uuid4(),
            tenant_id=proposal.tenant_id,
            proposal_id=proposal_id,
            selected_option_number=selected_option_number,
            status=DeploymentStatus.DRAFT,
            created_by=created_by,
            parameters=parameters or {}
        )
        
        # Generate Bicep template
        bicep_template = await self._generate_bicep_template(selected_option)
        deployment.bicep_template = bicep_template
        
        # Also generate ARM JSON (compiled Bicep)
        arm_template = await self._generate_arm_template(selected_option)
        deployment.arm_template = arm_template
        
        self.session.add(deployment)
        
        # Create deployment resources
        resources = selected_option.resources_json.get("resources", [])
        cost_estimates = selected_option.cost_estimate_json.get("estimates", [])
        
        for i, resource in enumerate(resources):
            # Find matching cost estimate
            cost_estimate = next(
                (ce for ce in cost_estimates if ce["service"] == resource["type"] and ce["sku"] == resource["sku"]),
                None
            )
            monthly_cost = Decimal(str(cost_estimate["monthly_cost"])) if cost_estimate else None
            
            dep_resource = DeploymentResource(
                id=uuid.uuid4(),
                deployment_id=deployment.id,
                resource_type=resource["type"],
                name=resource["name"],
                sku=resource.get("sku"),
                region=resource["region"],
                status=ResourceStatus.PENDING,
                monthly_cost=monthly_cost,
                properties=resource.get("properties", {})
            )
            self.session.add(dep_resource)
        
        # Log creation
        await self._log(deployment.id, LogLevel.INFO, "Deployment created", "deployment_service")
        
        deployment.status = DeploymentStatus.PROPOSED
        await self.session.commit()
        await self.session.refresh(deployment)
        
        return deployment
    
    async def review_deployment(
        self,
        deployment_id: uuid.UUID
    ) -> dict:
        """Get deployment review information.
        
        Args:
            deployment_id: Deployment ID
        
        Returns:
            Review information with resources, costs, warnings
        """
        stmt = select(DeploymentRequest).where(
            DeploymentRequest.id == deployment_id
        ).options(
            selectinload(DeploymentRequest.resources)
        )
        result = await self.session.execute(stmt)
        deployment = result.scalar_one()
        
        # Calculate totals
        total_resources = len(deployment.resources)
        total_monthly_cost = sum(
            (r.monthly_cost or Decimal("0.00")) for r in deployment.resources
        )
        
        # Build resource breakdown
        resource_breakdown = [
            {
                "name": r.name,
                "type": r.resource_type,
                "sku": r.sku,
                "region": r.region,
                "monthly_cost": float(r.monthly_cost) if r.monthly_cost else 0.0
            }
            for r in deployment.resources
        ]
        
        # Generate warnings
        warnings = []
        if total_monthly_cost > 500:
            warnings.append(f"High monthly cost: ${total_monthly_cost}")
        
        if total_resources > 20:
            warnings.append(f"Large number of resources: {total_resources}")
        
        return {
            "deployment_id": deployment_id,
            "total_resources": total_resources,
            "total_monthly_cost": float(total_monthly_cost),
            "resource_breakdown": resource_breakdown,
            "warnings": warnings,
            "bicep_template": deployment.bicep_template,
            "status": deployment.status
        }
    
    async def approve_deployment(
        self,
        deployment_id: uuid.UUID,
        approved_by: uuid.UUID
    ) -> DeploymentRequest:
        """Approve deployment for execution.
        
        Args:
            deployment_id: Deployment ID
            approved_by: User ID approving
        
        Returns:
            Updated deployment
        """
        stmt = select(DeploymentRequest).where(
            DeploymentRequest.id == deployment_id
        )
        result = await self.session.execute(stmt)
        deployment = result.scalar_one()
        
        # Validate state transition
        if deployment.status not in [DeploymentStatus.PROPOSED, DeploymentStatus.REVIEWED]:
            raise ValueError(f"Cannot approve deployment in status: {deployment.status}")
        
        # Update status
        deployment.status = DeploymentStatus.APPROVED
        deployment.approved_by = approved_by
        deployment.approved_at = datetime.utcnow()
        
        await self._log(deployment_id, LogLevel.INFO, "Deployment approved", "deployment_service")
        
        await self.session.commit()
        await self.session.refresh(deployment)
        
        return deployment
    
    async def execute_deployment(
        self,
        deployment_id: uuid.UUID
    ) -> DeploymentRequest:
        """Execute deployment (provision resources).
        
        For MVP, this is a structured stub that logs what would happen.
        In production, this would call Azure SDK to actually provision.
        
        Args:
            deployment_id: Deployment ID
        
        Returns:
            Updated deployment
        """
        stmt = select(DeploymentRequest).where(
            DeploymentRequest.id == deployment_id
        ).options(
            selectinload(DeploymentRequest.resources)
        )
        result = await self.session.execute(stmt)
        deployment = result.scalar_one()
        
        # Validate state
        if deployment.status != DeploymentStatus.APPROVED:
            raise ValueError(f"Cannot execute deployment in status: {deployment.status}")
        
        # Update status
        deployment.status = DeploymentStatus.PROVISIONING
        deployment.started_at = datetime.utcnow()
        
        await self._log(deployment_id, LogLevel.INFO, "Starting deployment execution", "deployment_service")
        
        await self.session.commit()
        
        try:
            # MVP: Log what would be deployed
            await self._log(deployment_id, LogLevel.INFO, "Validating Azure connection", "azure_sdk")
            await self._log(deployment_id, LogLevel.INFO, f"Creating resource group: {deployment.resource_group_name or 'rg-azurebuilder'}", "azure_sdk")
            
            # Process each resource
            for resource in deployment.resources:
                resource.status = ResourceStatus.CREATING
                await self._log(
                    deployment_id,
                    LogLevel.INFO,
                    f"Creating {resource.resource_type}: {resource.name} (SKU: {resource.sku})",
                    "azure_sdk",
                    resource.name
                )
                
                # Simulate deployment time
                # In production: await azure_sdk.create_resource(resource)
                
                resource.status = ResourceStatus.CREATED
                resource.azure_resource_id = f"/subscriptions/xxx/resourceGroups/rg-azurebuilder/providers/{resource.resource_type}/{resource.name}"
                
                await self._log(
                    deployment_id,
                    LogLevel.INFO,
                    f"Successfully created {resource.name}",
                    "azure_sdk",
                    resource.name
                )
            
            # Mark as deployed
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.completed_at = datetime.utcnow()
            deployment.azure_deployment_id = f"deployment-{uuid.uuid4()}"
            
            await self._log(deployment_id, LogLevel.INFO, "Deployment completed successfully", "deployment_service")
            
            await self.session.commit()
            await self.session.refresh(deployment)
            
            return deployment
            
        except Exception as e:
            # Handle failure
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            deployment.completed_at = datetime.utcnow()
            
            await self._log(deployment_id, LogLevel.ERROR, f"Deployment failed: {str(e)}", "deployment_service")
            
            await self.session.commit()
            raise
    
    async def rollback_deployment(
        self,
        deployment_id: uuid.UUID,
        rolled_back_by: uuid.UUID
    ) -> DeploymentRequest:
        """Rollback deployment (delete resources).
        
        Args:
            deployment_id: Deployment ID
            rolled_back_by: User ID performing rollback
        
        Returns:
            Updated deployment
        """
        stmt = select(DeploymentRequest).where(
            DeploymentRequest.id == deployment_id
        ).options(
            selectinload(DeploymentRequest.resources)
        )
        result = await self.session.execute(stmt)
        deployment = result.scalar_one()
        
        await self._log(deployment_id, LogLevel.WARNING, "Starting rollback", "deployment_service")
        
        # Delete resources in reverse order
        for resource in reversed(deployment.resources):
            if resource.status == ResourceStatus.CREATED:
                await self._log(
                    deployment_id,
                    LogLevel.INFO,
                    f"Deleting {resource.name}",
                    "azure_sdk",
                    resource.name
                )
                
                # In production: await azure_sdk.delete_resource(resource)
                resource.status = ResourceStatus.DELETED
        
        deployment.status = DeploymentStatus.ROLLED_BACK
        deployment.rolled_back_at = datetime.utcnow()
        deployment.rolled_back_by = rolled_back_by
        
        await self._log(deployment_id, LogLevel.INFO, "Rollback completed", "deployment_service")
        
        await self.session.commit()
        await self.session.refresh(deployment)
        
        return deployment
    
    async def get_execution_logs(
        self,
        deployment_id: uuid.UUID,
        limit: int = 100
    ) -> list[ExecutionLog]:
        """Get execution logs for deployment.
        
        Args:
            deployment_id: Deployment ID
            limit: Max logs to return
        
        Returns:
            List of execution logs
        """
        stmt = select(ExecutionLog).where(
            ExecutionLog.deployment_id == deployment_id
        ).order_by(
            ExecutionLog.sequence
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        
        return list(logs)
    
    async def _generate_bicep_template(
        self,
        option: ProposalOption
    ) -> str:
        """Generate Bicep template from proposal option.
        
        Args:
            option: Proposal option
        
        Returns:
            Bicep template as string
        """
        resources = option.resources_json.get("resources", [])
        
        # Build Bicep template
        lines = [
            "// Auto-generated Bicep template from Azure Builder",
            f"// Proposal Option: {option.name}",
            "",
            "param location string = 'eastus'",
            "param environment string = 'prod'",
            ""
        ]
        
        for resource in resources:
            resource_type = resource["type"]
            name = resource["name"]
            sku = resource.get("sku", "Standard")
            
            # Generate Bicep resource definition
            if resource_type == "App Service":
                lines.extend([
                    f"resource appService '{name}' 'Microsoft.Web/sites@2022-03-01' = {{",
                    f"  name: '{name}'",
                    f"  location: location",
                    "  properties: {",
                    f"    serverFarmId: appServicePlan.id",
                    "  }",
                    "}",
                    ""
                ])
            elif resource_type == "SQL Database":
                lines.extend([
                    f"resource sqlDatabase '{name}' 'Microsoft.Sql/servers/databases@2021-11-01' = {{",
                    f"  name: '{name}'",
                    f"  location: location",
                    "  sku: {",
                    f"    name: '{sku}'",
                    "  }",
                    "}",
                    ""
                ])
        
        return "\n".join(lines)
    
    async def _generate_arm_template(
        self,
        option: ProposalOption
    ) -> dict:
        """Generate ARM JSON template from proposal option.
        
        Args:
            option: Proposal option
        
        Returns:
            ARM template as dict
        """
        resources = option.resources_json.get("resources", [])
        
        arm_resources = []
        
        for resource in resources:
            arm_resource = {
                "type": f"Microsoft.{resource['type'].replace(' ', '')}",
                "apiVersion": "2022-03-01",
                "name": resource["name"],
                "location": "[parameters('location')]",
                "sku": {
                    "name": resource.get("sku", "Standard")
                },
                "properties": resource.get("properties", {})
            }
            arm_resources.append(arm_resource)
        
        return {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "location": {
                    "type": "string",
                    "defaultValue": "eastus"
                }
            },
            "resources": arm_resources,
            "outputs": {}
        }
    
    async def _log(
        self,
        deployment_id: uuid.UUID,
        level: LogLevel,
        message: str,
        source: str,
        resource_name: Optional[str] = None
    ):
        """Add execution log entry.
        
        Args:
            deployment_id: Deployment ID
            level: Log level
            message: Log message
            source: Log source
            resource_name: Optional resource name
        """
        # Get current sequence number
        stmt = select(ExecutionLog).where(
            ExecutionLog.deployment_id == deployment_id
        ).order_by(ExecutionLog.sequence.desc()).limit(1)
        result = await self.session.execute(stmt)
        last_log = result.scalar_one_or_none()
        
        sequence = (last_log.sequence + 1) if last_log else 1
        
        log = ExecutionLog(
            id=uuid.uuid4(),
            deployment_id=deployment_id,
            sequence=sequence,
            level=level,
            message=message,
            source=source,
            resource_name=resource_name
        )
        
        self.session.add(log)
        await self.session.flush()
