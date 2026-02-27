"""Template Service - Pre-built architecture templates."""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Template


class TemplateService:
    """Service for managing architecture templates."""
    
    def __init__(self, session: AsyncSession):
        """Initialize template service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def get_templates(
        self,
        category: Optional[str] = None,
        is_public: bool = True
    ) -> list[Template]:
        """Get all templates, optionally filtered by category.
        
        Args:
            category: Optional category filter
            is_public: Filter by public/private templates
        
        Returns:
            List of templates
        """
        stmt = select(Template).where(Template.is_public == is_public)
        
        if category:
            stmt = stmt.where(Template.category == category)
        
        stmt = stmt.order_by(Template.category, Template.name)
        
        result = await self.session.execute(stmt)
        templates = result.scalars().all()
        
        return list(templates)
    
    async def get_by_category(self) -> dict[str, list[Template]]:
        """Get templates grouped by category.
        
        Returns:
            Dict of category -> templates
        """
        templates = await self.get_templates()
        
        by_category = {}
        for template in templates:
            if template.category not in by_category:
                by_category[template.category] = []
            by_category[template.category].append(template)
        
        return by_category
    
    async def search(self, query: str) -> list[Template]:
        """Search templates by name, description, or tags.
        
        Args:
            query: Search query
        
        Returns:
            Matching templates
        """
        # Simple text search (in production, use full-text search)
        stmt = select(Template).where(
            (Template.name.ilike(f"%{query}%")) |
            (Template.description.ilike(f"%{query}%"))
        )
        
        result = await self.session.execute(stmt)
        templates = result.scalars().all()
        
        return list(templates)
    
    async def seed_templates(self):
        """Seed database with default templates.
        
        This should be called once during initial setup.
        """
        templates_data = [
            {
                "category": "web",
                "name": "Web Application (App Service + SQL)",
                "description": "Classic web application with App Service and SQL Database. Ideal for ASP.NET, Node.js, or Python web apps.",
                "base_architecture": "Simple 3-tier architecture with web tier (App Service), data tier (SQL Database), and storage (Storage Account).",
                "variants": {
                    "basic": {"sku": "B1", "monthly_cost": 55},
                    "standard": {"sku": "S1", "monthly_cost": 145},
                    "premium": {"sku": "P1V2", "monthly_cost": 250}
                },
                "resource_types": ["App Service", "App Service Plan", "SQL Database", "SQL Server", "Storage Account"],
                "estimated_cost_min": "$50",
                "estimated_cost_max": "$300",
                "difficulty": "beginner",
                "tags": ["web", "sql", "app-service"]
            },
            {
                "category": "microservices",
                "name": "Microservices (Container Apps + Service Bus)",
                "description": "Modern microservices architecture with Container Apps, Service Bus for messaging, and CosmosDB for data.",
                "base_architecture": "Event-driven microservices with Container Apps, Azure Service Bus for async messaging, CosmosDB for scalable data storage, and Application Gateway for ingress.",
                "variants": {
                    "basic": {"monthly_cost": 150},
                    "standard": {"monthly_cost": 400},
                    "enterprise": {"monthly_cost": 1200}
                },
                "resource_types": ["Container Apps", "Container App Environment", "Service Bus", "CosmosDB", "Application Gateway"],
                "estimated_cost_min": "$150",
                "estimated_cost_max": "$1500",
                "difficulty": "advanced",
                "tags": ["microservices", "containers", "cosmosdb", "messaging"]
            },
            {
                "category": "chatbot",
                "name": "Teams Chatbot (Bot Service + CosmosDB)",
                "description": "Microsoft Teams chatbot with Bot Service, App Service for web host, and CosmosDB for conversation state.",
                "base_architecture": "Bot Framework application hosted on App Service, registered with Bot Service, using CosmosDB for state storage and Application Insights for monitoring.",
                "variants": {
                    "basic": {"monthly_cost": 60},
                    "standard": {"monthly_cost": 200}
                },
                "resource_types": ["Bot Service", "App Service", "App Service Plan", "CosmosDB", "Application Insights"],
                "estimated_cost_min": "$60",
                "estimated_cost_max": "$250",
                "difficulty": "intermediate",
                "tags": ["chatbot", "teams", "bot-service"]
            },
            {
                "category": "data",
                "name": "Data Pipeline (Data Factory + Synapse)",
                "description": "ETL/ELT data pipeline with Data Factory for orchestration, Synapse for analytics, and Data Lake Storage.",
                "base_architecture": "Modern data platform with Azure Data Factory for data integration, Synapse Analytics for data warehousing, and Data Lake Storage Gen2 for raw data storage.",
                "variants": {
                    "basic": {"monthly_cost": 300},
                    "standard": {"monthly_cost": 1000},
                    "enterprise": {"monthly_cost": 3000}
                },
                "resource_types": ["Data Factory", "Synapse Analytics", "Storage Account (Data Lake)", "SQL Pool"],
                "estimated_cost_min": "$300",
                "estimated_cost_max": "$5000",
                "difficulty": "advanced",
                "tags": ["data", "etl", "synapse", "data-factory"]
            },
            {
                "category": "web",
                "name": "Static Website (Storage + CDN)",
                "description": "Cost-effective static website hosting with Storage Account static website feature and CDN for global distribution.",
                "base_architecture": "Storage Account configured for static website hosting, Azure CDN for caching and global distribution, optional Azure DNS for custom domain.",
                "variants": {
                    "basic": {"monthly_cost": 5},
                    "standard": {"monthly_cost": 25}
                },
                "resource_types": ["Storage Account", "CDN Profile", "CDN Endpoint", "DNS Zone"],
                "estimated_cost_min": "$5",
                "estimated_cost_max": "$50",
                "difficulty": "beginner",
                "tags": ["web", "static", "cdn", "storage"]
            },
            {
                "category": "serverless",
                "name": "Serverless API (Functions + CosmosDB + APIM)",
                "description": "Serverless API with Azure Functions for compute, CosmosDB for data, and API Management for gateway.",
                "base_architecture": "Azure Functions (consumption plan) for API logic, CosmosDB for data persistence, API Management for API gateway, and Application Insights for monitoring.",
                "variants": {
                    "basic": {"monthly_cost": 100},
                    "standard": {"monthly_cost": 350},
                    "premium": {"monthly_cost": 800}
                },
                "resource_types": ["Azure Functions", "Function App", "CosmosDB", "API Management", "Application Insights"],
                "estimated_cost_min": "$100",
                "estimated_cost_max": "$1000",
                "difficulty": "intermediate",
                "tags": ["serverless", "functions", "api", "cosmosdb"]
            },
            {
                "category": "compute",
                "name": "VM Workload (VM Scale Set + Load Balancer)",
                "description": "Scalable VM-based workload with VM Scale Set, Load Balancer, and managed disks.",
                "base_architecture": "Virtual Machine Scale Set for auto-scaling compute, Load Balancer for traffic distribution, managed disks for storage, and Network Security Group for security.",
                "variants": {
                    "basic": {"vm_sku": "Standard_B2s", "monthly_cost": 100},
                    "standard": {"vm_sku": "Standard_D4s_v3", "monthly_cost": 400},
                    "premium": {"vm_sku": "Standard_E8s_v3", "monthly_cost": 800}
                },
                "resource_types": ["Virtual Machine Scale Set", "Load Balancer", "Virtual Network", "Network Security Group", "Managed Disk"],
                "estimated_cost_min": "$100",
                "estimated_cost_max": "$1500",
                "difficulty": "intermediate",
                "tags": ["vm", "compute", "scale-set", "load-balancer"]
            },
            {
                "category": "ai",
                "name": "AI/ML Platform (OpenAI + Cognitive Services)",
                "description": "AI platform with Azure OpenAI, Cognitive Services, and storage for ML models and data.",
                "base_architecture": "Azure OpenAI Service for LLMs, Cognitive Services for pre-built AI, Storage Account for data and models, optional Azure ML for training.",
                "variants": {
                    "basic": {"monthly_cost": 200},
                    "standard": {"monthly_cost": 800},
                    "enterprise": {"monthly_cost": 3000}
                },
                "resource_types": ["Azure OpenAI", "Cognitive Services", "Storage Account", "Azure ML Workspace"],
                "estimated_cost_min": "$200",
                "estimated_cost_max": "$5000",
                "difficulty": "advanced",
                "tags": ["ai", "ml", "openai", "cognitive-services"]
            }
        ]
        
        for data in templates_data:
            # Check if template already exists
            stmt = select(Template).where(
                Template.name == data["name"],
                Template.is_public == True
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                template = Template(
                    id=uuid.uuid4(),
                    is_public=True,
                    **data,
                    template_data=data  # Store full data for reference
                )
                self.session.add(template)
        
        await self.session.commit()
