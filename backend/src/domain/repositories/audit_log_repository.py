from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.entities.audit_log import AuditLog


class AuditLogRepository(ABC):
    @abstractmethod
    async def create(
        self,
        actor_id: Optional[UUID],
        action: str,
        entity_type: str,
        entity_id: str,
        timestamp: datetime,
        reason: str,
    ) -> AuditLog:
        """Create an audit log entry."""
        ...
