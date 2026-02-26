"""Template service for pre-built infrastructure patterns."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Template


class TemplateService:
    """Service for managing infrastructure templates."""

    @staticmethod
    async def get_public_templates(db: AsyncSession) -> list[Template]:
        """
        Get all public templates.
        
        Args:
            db: Database session
            
        Returns:
            List of public templates
        """
        result = await db.execute(
            select(Template)
            .where(Template.is_public == True)
            .order_by(Template.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_tenant_templates(db: AsyncSession, tenant_id: UUID) -> list[Template]:
        """
        Get templates for a specific tenant (public + tenant-specific).
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            
        Returns:
            List of templates
        """
        result = await db.execute(
            select(Template)
            .where(
                (Template.is_public == True) |
                (Template.tenant_id == tenant_id)
            )
            .order_by(Template.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_template_by_id(db: AsyncSession, template_id: UUID) -> Optional[Template]:
        """
        Get a template by ID.
        
        Args:
            db: Database session
            template_id: Template UUID
            
        Returns:
            Template or None
        """
        result = await db.execute(
            select(Template).where(Template.id == template_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_template(
        db: AsyncSession,
        name: str,
        description: str,
        category: str,
        difficulty: str,
        template_data: dict,
        tenant_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
        is_public: bool = False,
    ) -> Template:
        """
        Create a new template.
        
        Args:
            db: Database session
            name: Template name
            description: Template description
            category: Category (web, data, ai, etc.)
            difficulty: Difficulty level (beginner, intermediate, advanced)
            template_data: Template definition (commands, parameters, etc.)
            tenant_id: Optional tenant ID for private templates
            created_by: Optional creator user ID
            is_public: Whether template is public
            
        Returns:
            Created template
        """
        template = Template(
            name=name,
            description=description,
            category=category,
            difficulty=difficulty,
            template_data=template_data,
            tenant_id=tenant_id,
            created_by=created_by,
            is_public=is_public,
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        return template
