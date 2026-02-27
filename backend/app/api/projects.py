"""Projects API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_with_tenant_context, require_permission
from app.models.project import Project
from app.models.user import User
from app.schemas.project import Project as ProjectSchema, ProjectCreate, ProjectUpdate

router = APIRouter()


@router.get("/", response_model=list[ProjectSchema])
async def list_projects(
    db: AsyncSession = Depends(get_db_with_tenant_context),
    current_user: User = Depends(get_current_user),
):
    """List all projects for the current tenant."""
    result = await db.execute(
        select(Project).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectSchema.model_validate(p) for p in projects]


@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db_with_tenant_context),
    current_user: User = Depends(require_permission("project:create")),
):
    """Create a new project."""
    project = Project(
        tenant_id=current_user.tenant_id,
        name=project_data.name,
        description=project_data.description,
        created_by=current_user.id,
        tags=project_data.tags,
        project_metadata=project_data.project_metadata,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectSchema.model_validate(project)


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant_context),
    current_user: User = Depends(get_current_user),
):
    """Get a project by ID."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return ProjectSchema.model_validate(project)


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db_with_tenant_context),
    current_user: User = Depends(require_permission("project:update")),
):
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Update fields
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.tags is not None:
        project.tags = project_data.tags
    if project_data.project_metadata is not None:
        project.project_metadata = project_data.project_metadata

    await db.commit()
    await db.refresh(project)

    return ProjectSchema.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant_context),
    current_user: User = Depends(require_permission("project:delete")),
):
    """Delete a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    await db.delete(project)
    await db.commit()

    return None
