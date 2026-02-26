"""User model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class User(Base):
    """User in the system."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="viewer")  # owner, admin, operator, viewer
    azure_ad_oid = Column(String(255), unique=True, nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    projects_created = relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    conversations_created = relationship("Conversation", back_populates="creator")
    executions_started = relationship("Execution", back_populates="starter")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def is_owner(self) -> bool:
        """Check if user is tenant owner."""
        return self.role == "owner"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin or owner."""
        return self.role in ("owner", "admin")

    @property
    def can_execute(self) -> bool:
        """Check if user can execute commands."""
        return self.role in ("owner", "admin", "operator")
