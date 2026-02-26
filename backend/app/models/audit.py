"""Audit log model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class AuditLog(Base):
    """Immutable audit log for compliance and security."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # NULL for system events
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default="info")  # info, warning, critical

    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, severity={self.severity})>"
