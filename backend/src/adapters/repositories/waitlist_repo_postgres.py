from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.waitlist import Waitlist
from domain.repositories.waitlist_repository import WaitlistRepository
from domain.value_objects.time_slot import TimeSlot
from infra.models import WaitlistORM


class WaitlistRepositoryPostgres(WaitlistRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_workspace_employee(
        self, workspace_id: UUID, employee_id: UUID
    ) -> Waitlist | None:
        result = await self.session.execute(
            select(WaitlistORM).where(
                WaitlistORM.workspace_id == workspace_id,
                WaitlistORM.employee_id == employee_id,
            )
        )
        row = result.scalars().first()
        if not row:
            return None
        return self._to_entity(row)

    async def create(
        self, workspace_id: UUID, employee_id: UUID, desired_slot: TimeSlot
    ) -> Waitlist:
        orm = WaitlistORM(
            workspace_id=workspace_id,
            employee_id=employee_id,
            desired_start=desired_slot.start,
            desired_end=desired_slot.end,
        )
        self.session.add(orm)
        await self.session.flush()
        return self._to_entity(orm)

    async def save(self, entry: Waitlist) -> Waitlist:
        row = await self.session.get(WaitlistORM, entry.id)
        if row is None:
            raise LookupError("Waitlist entry not found")
        row.notified_at = entry.notified_at
        await self.session.flush()
        return entry

    async def delete(self, waitlist_id: UUID) -> None:
        await self.session.execute(sql_delete(WaitlistORM).where(WaitlistORM.id == waitlist_id))

    async def list_all_by_workspace(self, workspace_id: UUID) -> list[Waitlist]:
        result = await self.session.execute(
            select(WaitlistORM)
            .where(WaitlistORM.workspace_id == workspace_id)
            .order_by(WaitlistORM.created_at, WaitlistORM.id)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    @staticmethod
    def _to_entity(row: WaitlistORM) -> Waitlist:
        def aware_utc(value: datetime | None) -> datetime | None:
            if value is None:
                return None
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)

        return Waitlist(
            id=row.id,
            workspace_id=row.workspace_id,
            employee_id=row.employee_id,
            desired_slot_start=aware_utc(row.desired_start),
            desired_slot_end=aware_utc(row.desired_end),
            created_at=aware_utc(row.created_at),
            notified_at=aware_utc(row.notified_at),
        )
