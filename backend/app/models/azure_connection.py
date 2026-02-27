"""Azure connection model for customer Azure subscriptions."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class AuthMethod(str, enum.Enum):
    """Azure authentication method."""
    SERVICE_PRINCIPAL = "service_principal"
    MANAGED_IDENTITY = "managed_identity"


class ConnectionStatus(str, enum.Enum):
    """Azure connection status."""
    PENDING = "pending"
    VALIDATING = "validating"
    ACTIVE = "active"
    FAILED = "failed"
    EXPIRED = "expired"


class AzureConnection(Base):
    """Customer's Azure subscription connection.
    
    Stores connection details and credentials reference
    (actual credentials stored in Azure Key Vault).
    """
    __tablename__ = "azure_connections"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Azure subscription details
    subscription_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    azure_tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Authentication method
    auth_method: Mapped[AuthMethod] = mapped_column(
        SQLEnum(AuthMethod, native_enum=False, length=30),
        nullable=False,
        default=AuthMethod.SERVICE_PRINCIPAL
    )
    
    # Reference to credentials stored in Azure Key Vault
    # Format: "tenant-{tenant_id}-azure-connection-{id}"
    key_vault_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Connection status
    status: Mapped[ConnectionStatus] = mapped_column(
        SQLEnum(ConnectionStatus, native_enum=False, length=20),
        nullable=False,
        default=ConnectionStatus.PENDING,
        index=True
    )
    
    # Validation details
    last_validated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    # Subscription quotas and limits (cached)
    quotas: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Additional metadata (renamed to avoid SQLAlchemy reserved word conflict)
    connection_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
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
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="azure_connections")
    
    def __repr__(self) -> str:
        return f"<AzureConnection(id={self.id}, subscription={self.subscription_id}, status={self.status})>"
