"""Audit logging service."""
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for comprehensive audit logging."""

    @staticmethod
    async def log_event(
        db: AsyncSession,
        tenant_id: UUID,
        event_type: str,
        event_data: dict[str, Any],
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info",
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            event_type: Event type (e.g., 'user_login', 'command_executed')
            event_data: Event-specific data
            user_id: Optional user UUID
            ip_address: Optional IP address
            user_agent: Optional user agent string
            severity: Severity level (info, warning, critical)
            
        Returns:
            Created audit log entry
        """
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        logger.info(
            f"Audit log created: {event_type}",
            extra={
                "tenant_id": str(tenant_id),
                "user_id": str(user_id) if user_id else None,
                "event_type": event_type,
                "severity": severity,
            }
        )

        return audit_log

    @staticmethod
    async def log_user_login(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log user login event."""
        return await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="user_login",
            event_data={"action": "login"},
            ip_address=ip_address,
            user_agent=user_agent,
            severity="info",
        )

    @staticmethod
    async def log_command_generated(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: UUID,
        natural_language_input: str,
        generated_commands: list[dict[str, Any]],
        risk_level: str,
    ) -> AuditLog:
        """Log AI command generation event."""
        return await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="command_generated",
            event_data={
                "conversation_id": str(conversation_id),
                "natural_language_input": natural_language_input,
                "commands_count": len(generated_commands),
                "risk_level": risk_level,
            },
            severity="info",
        )

    @staticmethod
    async def log_execution_started(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        execution_id: UUID,
        commands_count: int,
    ) -> AuditLog:
        """Log execution start event."""
        return await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="execution_started",
            event_data={
                "execution_id": str(execution_id),
                "commands_count": commands_count,
            },
            severity="info",
        )

    @staticmethod
    async def log_execution_completed(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        execution_id: UUID,
        status: str,
        duration_seconds: float,
    ) -> AuditLog:
        """Log execution completion event."""
        return await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="execution_completed",
            event_data={
                "execution_id": str(execution_id),
                "status": status,
                "duration_seconds": duration_seconds,
            },
            severity="warning" if status == "failed" else "info",
        )

    @staticmethod
    async def log_settings_changed(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        changes: dict[str, Any],
    ) -> AuditLog:
        """Log settings change event."""
        return await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="settings_changed",
            event_data={"changes": changes},
            severity="warning",
        )

    @staticmethod
    async def get_recent_logs(
        db: AsyncSession,
        tenant_id: UUID,
        limit: int = 50,
    ) -> list[AuditLog]:
        """
        Get recent audit logs for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            limit: Maximum number of logs to return
            
        Returns:
            List of audit logs
        """
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
