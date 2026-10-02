from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories.audit_log_repository import AuditLogRepository
from domain.entities.audit_log import AuditLog
from infra.models import AuditLogORM


class AuditLogRepositoryPostgres(AuditLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, actor_id: UUID, action: str, entity_type: str, entity_id: str, timestamp: datetime, reason: str) -> AuditLog:
        orm = AuditLogORM(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=timestamp,
            reason=reason,
        )
        self.session.add(orm)
        await self.session.commit()
        return AuditLog(id=orm.id, actor_id=actor_id, action=action, entity_type=entity_type, entity_id=entity_id, timestamp=timestamp, reason=reason)