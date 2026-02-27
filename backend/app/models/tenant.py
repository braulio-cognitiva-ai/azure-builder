"""Tenant model for multi-tenancy support."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.audit import AuditLog
    from app.models.azure_connection import AzureConnection


class Tenant(Base):
    """Tenant model with multi-tenancy support.
    
    Each tenant represents an organization/team using the platform.
    """
    __tablename__ = "tenants"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Plan tier: free, pro, enterprise
    plan_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    
    # Tenant-specific settings (JSON)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Azure subscription ID (optional, for tracking)
    azure_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")
    azure_connections: Mapped[list["AzureConnection"]] = relationship("AzureConnection", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, plan={self.plan_tier})>"
