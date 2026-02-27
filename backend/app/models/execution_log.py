"""Execution log model for real-time deployment logs."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SQLEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UUID

if TYPE_CHECKING:
    from app.models.deployment import DeploymentRequest


class LogLevel(str, enum.Enum):
    """Log level for execution logs."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ExecutionLog(Base):
    """Real-time execution log entries per deployment.
    
    Captures detailed logs during deployment provisioning
    for debugging and monitoring.
    """
    __tablename__ = "execution_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("deployment_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Log sequence number (for ordering)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Log level
    level: Mapped[LogLevel] = mapped_column(
        SQLEnum(LogLevel, native_enum=False, length=20),
        nullable=False,
        default=LogLevel.INFO
    )
    
    # Log message
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Component/source that generated the log (e.g., "bicep_compiler", "azure_sdk", "deployment_service")
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Related resource name (if applicable)
    resource_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    deployment: Mapped["DeploymentRequest"] = relationship("DeploymentRequest", back_populates="execution_logs")
    
    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, level={self.level}, message={self.message[:50]}...)>"
