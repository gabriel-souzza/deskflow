from uuid import UUID
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from domain.repositories.waitlist_repository import WaitlistRepository
from domain.entities.waitlist import Waitlist
from infra.models import WaitlistORM


class WaitlistRepositoryPostgres(WaitlistRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_workspace_employee(self, workspace_id: UUID, employee_id: UUID) -> Optional[Waitlist]:
        result = await self.session.execute(
            select(WaitlistORM).where(
                WaitlistORM.workspace_id == workspace_id,
                WaitlistORM.employee_id == employee_id,
            )
        )
        row = result.scalars().first()
        if not row:
            return None
        return Waitlist(id=row.id, workspace_id=row.workspace_id, employee_id=row.employee_id, desired_slot_start=row.desired_start, desired_slot_end=row.desired_end, created_at=row.created_at, notified_at=row.notified_at)

    async def create(self, workspace_id: UUID, employee_id: UUID, desired_slot_start: datetime, desired_slot_end: datetime) -> Waitlist:
        orm = WaitlistORM(
            workspace_id=workspace_id,
            employee_id=employee_id,
            desired_start=desired_slot_start,
            desired_end=desired_slot_end,
        )
        self.session.add(orm)
        await self.session.commit()
        return Waitlist(id=orm.id, workspace_id=workspace_id, employee_id=employee_id, desired_slot_start=desired_slot_start, desired_slot_end=desired_slot_end, created_at=orm.created_at)

    async def delete(self, waitlist_id: UUID) -> None:
        pass

    async def list_all_by_workspace(self, workspace_id: UUID) -> List[Waitlist]:
        result = await self.session.execute(
            select(WaitlistORM).where(WaitlistORM.workspace_id == workspace_id)
        )
        rows = result.scalars().all()
        return [Waitlist(id=r.id, workspace_id=r.workspace_id, employee_id=r.employee_id, desired_slot_start=r.desired_start, desired_slot_end=r.desired_end, created_at=r.created_at, notified_at=r.notified_at) for r in rows]