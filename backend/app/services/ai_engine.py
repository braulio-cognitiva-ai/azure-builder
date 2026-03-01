"""AI Engine Service - The Brain of Azure Builder.

This service translates natural language requests into Azure architecture
proposals with multiple options, each with diagrams, cost estimates, and recommendations.
"""
import json
import uuid
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    ArchitectureProposal,
    ProposalOption,
    ProposalStatus,
    Project
)
from app.schemas.proposal import (
    CostEstimate,
    ResourceDefinition,
    ProsCons,
    ProposalOptionCreate
)
from app.services.pricing_service import PricingService
from app.services.security_validator import SecurityValidator, validate_security
from app.services.quota_checker import QuotaCheckerService, QuotaStatus
from app.services.resource_discovery import ResourceDiscoveryService


# =============================================================================
# SYSTEM PROMPT - The Core IP of Azure Builder
# =============================================================================

SYSTEM_PROMPT = """You are an expert Azure Solution Architect with deep knowledge of:
- Azure Well-Architected Framework (reliability, security, cost optimization, operational excellence, performance)
- Azure services, SKUs, pricing, and regional availability
- Common architecture patterns (web apps, microservices, data platforms, AI/ML)
- Infrastructure-as-Code with Bicep and ARM templates

Your job: Given a user's natural language request, generate 2-3 architecture options with different trade-offs.

**RULES:**

1. **Output Structure:** Return ONLY valid JSON matching this schema:
   {
     "options": [
       {
         "option_number": 1,
         "name": "Option Name (e.g., Basic Web App)",
         "description": "Detailed description of this architecture approach",
         "architecture_diagram": "ASCII diagram showing components and connections",
         "resources": [
           {
             "type": "App Service",
             "name": "app-myapp-prod",
             "sku": "P1V2",
             "region": "eastus",
             "properties": {
               "runtime": "dotnet",
               "always_on": true
             }
           }
         ],
         "pros": ["Fast deployment", "Cost-effective for small traffic"],
         "cons": ["Limited scalability", "No built-in caching"]
       }
     ]
   }

2. **Architecture Diagrams:**
   - Use Mermaid.js syntax for visual diagrams
   - Show data flow and dependencies with arrows
   - Use graph TB (top-bottom) or LR (left-right) layout
   - Example:
     ```mermaid
     graph TB
         Client[Client/Browser]
         AppService[App Service<br/>P1V2]
         SQL[(SQL Database<br/>S1)]
         Storage[Storage Account]
         KeyVault[Key Vault]
         
         Client -->|HTTPS| AppService
         AppService -->|Query| SQL
         AppService -->|Store Files| Storage
         AppService -->|Get Secrets| KeyVault
     ```
   - Use subgraphs for resource groups or networks
   - Include SKU info in node labels where relevant

3. **Resource Naming:**
   - Follow Azure conventions: lowercase, hyphens allowed, 3-24 chars
   - Use prefixes: `app-`, `sql-`, `st-` (storage), `kv-` (key vault), etc.
   - Include environment suffix: `-dev`, `-prod`
   - Example: `app-ecommerce-prod`, `sql-orders-prod`

4. **SKU Selection:**
   - Option 1 (Basic/Standard): Lowest cost, basic features, suitable for dev/small prod
   - Option 2 (Premium): Balanced cost/performance, auto-scaling, high availability
   - Option 3 (Enterprise/Advanced): Maximum performance, multi-region, advanced features
   - Always specify exact SKU names (e.g., "P1V2", "S1", "GP_Gen5_2")

5. **Security Defaults:**
   - Always propose: Private endpoints, NSGs, managed identities, Key Vault for secrets
   - Enable: TLS/HTTPS, Azure AD auth, diagnostic logging
   - Avoid: Public endpoints without justification, weak authentication

6. **Regions:**
   - Default to `eastus` unless user specifies otherwise
   - For multi-region: `eastus` + `westus2` or `westeurope`
   - Consider data residency (GDPR for EU customers)

7. **Cost Consciousness:**
   - Basic option: <$100/month target
   - Premium option: $100-500/month
   - Enterprise option: >$500/month
   - Mention reserved instances / savings plans where applicable

8. **Completeness:**
   - Include ALL necessary resources (networking, monitoring, identity)
   - Don't forget: Application Insights, Log Analytics, NSGs, private endpoints
   - If user wants AI: Suggest Azure OpenAI, Cognitive Services, or Azure ML

9. **Context Awareness:**
   - If user mentions existing infrastructure, integrate with it
   - If budget is specified, stay within limits
   - If compliance mentioned (HIPAA, SOC2), add required controls

10. **Validation:**
    - Ensure resource names are unique across options
    - Verify SKUs exist and are available in specified regions
    - Check dependencies (e.g., App Service requires App Service Plan)

**EXAMPLE INPUT:**
"I need a web application that handles user auth and stores data in SQL. Budget is around $200/month."

**EXAMPLE OUTPUT:**
{
  "options": [
    {
      "option_number": 1,
      "name": "Basic Web App with SQL",
      "description": "Single-region deployment with App Service Basic tier and SQL Database Basic tier. Suitable for development and small production workloads with <1000 daily users. No auto-scaling or redundancy.",
      "architecture_diagram": "┌─────────┐\\n│ Client  │\\n└────┬────┘\\n     │\\n     ▼\\n┌─────────────────┐\\n│  App Service    │\\n│  (B1)           │\\n│  East US        │\\n└────┬────────────┘\\n     │\\n     ▼\\n┌─────────────────┐\\n│ SQL Database    │\\n│ (Basic, 5 DTU)  │\\n│ East US         │\\n└─────────────────┘",
      "resources": [
        {"type": "App Service Plan", "name": "plan-webapp-prod", "sku": "B1", "region": "eastus", "properties": {}},
        {"type": "App Service", "name": "app-webapp-prod", "sku": "B1", "region": "eastus", "properties": {"runtime": "node", "always_on": false}},
        {"type": "SQL Server", "name": "sql-webapp-prod", "sku": "Basic", "region": "eastus", "properties": {"admin_user": "sqladmin"}},
        {"type": "SQL Database", "name": "db-webapp-prod", "sku": "Basic", "region": "eastus", "properties": {"max_size_gb": 2}}
      ],
      "pros": ["Lowest cost (~$55/month)", "Simple architecture", "Easy to deploy", "Managed services reduce ops overhead"],
      "cons": ["No auto-scaling", "Single point of failure", "Limited to 1 GB RAM", "5 DTU may be slow under load"]
    }
  ]
}

**NOW PROCESS THE USER REQUEST BELOW AND GENERATE OPTIONS:**
"""


class AIEngineService:
    """AI Engine Service for architecture generation."""
    
    def __init__(self, session: AsyncSession):
        """Initialize AI engine service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.pricing_service = PricingService(session)
        
        # Initialize OpenAI client
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            self.client = AsyncOpenAI(
                api_key=settings.azure_openai_api_key,
                base_url=f"{settings.azure_openai_endpoint}/openai/deployments/{settings.azure_openai_deployment_name}",
                api_version=settings.azure_openai_api_version
            )
        else:
            # Fallback to OpenAI (for development)
            self.client = AsyncOpenAI()
    
    async def generate_proposal(
        self,
        project: Project,
        user_request: str,
        context: Optional[dict] = None
    ) -> ArchitectureProposal:
        """Generate architecture proposal with multiple options.
        
        Args:
            project: Project to associate proposal with
            user_request: User's natural language request
            context: Optional context (subscription limits, existing infrastructure, etc.)
        
        Returns:
            ArchitectureProposal with options
        """
        # Create proposal record
        proposal = ArchitectureProposal(
            id=uuid.uuid4(),
            project_id=project.id,
            tenant_id=project.tenant_id,
            user_request=user_request,
            status=ProposalStatus.GENERATING
        )
        self.session.add(proposal)
        await self.session.commit()
        
        try:
            # Build context including project budget
            if context is None:
                context = {}
            if project.budget_limit:
                context["budget"] = float(project.budget_limit)
            
            # Build context-aware prompt
            context_str = self._build_context_prompt(context) if context else ""
            full_prompt = f"{context_str}\n\nUSER REQUEST:\n{user_request}"
            
            # Call AI model
            response = await self.client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            ai_output = json.loads(response.choices[0].message.content)
            options_data = ai_output.get("options", [])
            
            # Create proposal options with cost estimates, security validation, and quota checks
            for option_data in options_data:
                # Estimate costs for each resource
                resources = option_data.get("resources", [])
                cost_estimates = await self._estimate_costs(resources)
                
                total_monthly_cost = sum(est["monthly_cost"] for est in cost_estimates)
                
                # Validate security
                security_report = await self._validate_security(resources)
                
                # Check quotas (if Azure connection available in context)
                quota_report = None
                if context and context.get("azure_connection"):
                    quota_report = await self._check_quotas(resources, context["azure_connection"])
                
                # Check if option exceeds budget
                budget_exceeded = False
                if project.budget_limit and total_monthly_cost > float(project.budget_limit):
                    budget_exceeded = True
                
                option = ProposalOption(
                    id=uuid.uuid4(),
                    proposal_id=proposal.id,
                    option_number=option_data["option_number"],
                    name=option_data["name"],
                    description=option_data["description"],
                    architecture_diagram=option_data["architecture_diagram"],
                    resources_json={"resources": resources},
                    cost_estimate_json={"estimates": cost_estimates},
                    pros_cons_json={
                        "pros": option_data.get("pros", []),
                        "cons": option_data.get("cons", []),
                        "security_report": security_report,
                        "quota_report": quota_report,
                        "budget_exceeded": budget_exceeded
                    },
                    monthly_cost=total_monthly_cost
                )
                self.session.add(option)
            
            # Update proposal status
            proposal.status = ProposalStatus.READY
            await self.session.commit()
            await self.session.refresh(proposal)
            
            return proposal
            
        except Exception as e:
            # Mark proposal as failed
            proposal.status = ProposalStatus.FAILED
            proposal.error_message = str(e)
            await self.session.commit()
            raise
    
    async def refine_proposal(
        self,
        proposal: ArchitectureProposal,
        feedback: str
    ) -> ArchitectureProposal:
        """Refine existing proposal based on user feedback.
        
        Args:
            proposal: Existing proposal
            feedback: User's refinement feedback
        
        Returns:
            Updated proposal
        """
        # Build conversation history
        conversation_history = [
            {"role": "user", "content": proposal.user_request},
            # AI response would be here but we don't store it
            {"role": "user", "content": f"REFINEMENT REQUEST: {feedback}"}
        ]
        
        # Regenerate with feedback
        try:
            response = await self.client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *conversation_history
                ],
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Clear old options
            for option in proposal.options:
                await self.session.delete(option)
            
            # Parse and create new options
            ai_output = json.loads(response.choices[0].message.content)
            options_data = ai_output.get("options", [])
            
            for option_data in options_data:
                resources = option_data.get("resources", [])
                cost_estimates = await self._estimate_costs(resources)
                total_monthly_cost = sum(est["monthly_cost"] for est in cost_estimates)
                
                # Validate security
                security_report = await self._validate_security(resources)
                
                # Get project for budget check
                project = await self.session.get(Project, proposal.project_id)
                budget_exceeded = False
                if project and project.budget_limit and total_monthly_cost > float(project.budget_limit):
                    budget_exceeded = True
                
                option = ProposalOption(
                    id=uuid.uuid4(),
                    proposal_id=proposal.id,
                    option_number=option_data["option_number"],
                    name=option_data["name"],
                    description=option_data["description"],
                    architecture_diagram=option_data["architecture_diagram"],
                    resources_json={"resources": resources},
                    cost_estimate_json={"estimates": cost_estimates},
                    pros_cons_json={
                        "pros": option_data.get("pros", []),
                        "cons": option_data.get("cons", []),
                        "security_report": security_report,
                        "budget_exceeded": budget_exceeded
                    },
                    monthly_cost=total_monthly_cost
                )
                self.session.add(option)
            
            proposal.status = ProposalStatus.READY
            await self.session.commit()
            await self.session.refresh(proposal)
            
            return proposal
            
        except Exception as e:
            proposal.status = ProposalStatus.FAILED
            proposal.error_message = str(e)
            await self.session.commit()
            raise
    
    def _build_context_prompt(self, context: dict) -> str:
        """Build context-aware prompt segment."""
        parts = ["ADDITIONAL CONTEXT:"]
        
        if "budget" in context:
            parts.append(f"- Budget constraint: ${context['budget']}/month")
        
        if "subscription_quotas" in context:
            parts.append("- Current subscription quotas: " + json.dumps(context["subscription_quotas"]))
        
        if "existing_resources" in context:
            parts.append("- Existing resources to integrate: " + json.dumps(context["existing_resources"]))
        
        if "compliance" in context:
            parts.append(f"- Compliance requirements: {', '.join(context['compliance'])}")
        
        return "\n".join(parts)
    
    async def _estimate_costs(self, resources: list[dict]) -> list[dict]:
        """Estimate costs for resources.
        
        Args:
            resources: List of resource definitions
        
        Returns:
            List of cost estimates
        """
        estimates = []
        
        for resource in resources:
            try:
                # Get pricing from pricing service
                price = await self.pricing_service.get_price(
                    service=resource["type"],
                    sku=resource["sku"],
                    region=resource["region"]
                )
                
                # Calculate monthly cost (assuming 730 hours/month)
                monthly_cost = price * 730 if price else 0.0
                
                estimates.append({
                    "service": resource["type"],
                    "sku": resource["sku"],
                    "region": resource["region"],
                    "quantity": 1,
                    "unit_price": float(price) if price else 0.0,
                    "monthly_cost": float(monthly_cost),
                    "unit": "hour"
                })
            except Exception:
                # If pricing fails, provide estimate of 0
                estimates.append({
                    "service": resource["type"],
                    "sku": resource["sku"],
                    "region": resource["region"],
                    "quantity": 1,
                    "unit_price": 0.0,
                    "monthly_cost": 0.0,
                    "unit": "hour"
                })
        
        return estimates
    
    async def _validate_security(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate security of proposed resources.
        
        Args:
            resources: List of resource definitions from AI
        
        Returns:
            Security report as dict
        """
        # Convert raw resources to ResourceDefinition objects
        resource_defs = []
        for res in resources:
            resource_defs.append(ResourceDefinition(
                type=res.get("type", ""),
                name=res.get("name", ""),
                sku=res.get("sku", ""),
                region=res.get("region", "eastus"),
                properties=res.get("properties", {})
            ))
        
        # Run security validation
        validator = SecurityValidator()
        report = validator.validate_proposal(resource_defs)
        
        # Convert to dict for JSON storage
        return {
            "score": report.score,
            "passed_checks": report.passed_checks,
            "total_checks": report.total_checks,
            "has_critical": report.has_critical,
            "has_high": report.has_high,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "resource_type": issue.resource_type,
                    "resource_name": issue.resource_name,
                    "issue": issue.issue,
                    "recommendation": issue.recommendation,
                    "doc_link": issue.doc_link
                }
                for issue in report.issues
            ]
        }
    
    async def _check_quotas(self, resources: List[Dict[str, Any]], azure_connection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check Azure subscription quotas for proposed resources.
        
        Args:
            resources: List of resource definitions from AI
            azure_connection: Azure connection info (subscription_id, credentials)
        
        Returns:
            Quota report as dict or None if check fails
        """
        try:
            # Convert raw resources to ResourceDefinition objects
            resource_defs = []
            for res in resources:
                resource_defs.append(ResourceDefinition(
                    type=res.get("type", ""),
                    name=res.get("name", ""),
                    sku=res.get("sku", ""),
                    region=res.get("region", "eastus"),
                    properties=res.get("properties", {})
                ))
            
            # Create quota checker
            checker = QuotaCheckerService(
                subscription_id=azure_connection["subscription_id"],
                tenant_id=azure_connection.get("tenant_id"),
                client_id=azure_connection.get("client_id"),
                client_secret=azure_connection.get("client_secret")
            )
            
            # Check quotas
            report = await checker.check_quotas(
                resources=resource_defs,
                region=resource_defs[0].region if resource_defs else "eastus"
            )
            
            await checker.close()
            
            # Convert to dict for JSON storage
            return {
                "overall_status": report.overall_status.value,
                "can_deploy": report.can_deploy,
                "warnings": report.warnings,
                "errors": report.errors,
                "checks": [
                    {
                        "resource_type": check.resource_type,
                        "quota_name": check.quota_name,
                        "current_usage": check.current_usage,
                        "quota_limit": check.quota_limit,
                        "requested": check.requested,
                        "available": check.available,
                        "after_deployment": check.after_deployment,
                        "status": check.status.value,
                        "message": check.message
                    }
                    for check in report.checks
                ]
            }
        
        except Exception as e:
            # If quota check fails, return None (don't block proposal)
            print(f"Quota check failed: {e}")
            return None
