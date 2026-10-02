from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories.availability_window_repository import AvailabilityWindowRepository
from domain.entities.availability_window import AvailabilityWindow
from domain.value_objects.capacity import Capacity
from infra.models import AvailabilityWindowORM


class AvailabilityWindowRepositoryPostgres(AvailabilityWindowRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_key(
        self, workspace_id: UUID, day: str, slot_index: int
    ) -> Optional[AvailabilityWindow]:
        result = await self.session.execute(
            select(AvailabilityWindowORM).where(
                AvailabilityWindowORM.workspace_id == workspace_id,
                AvailabilityWindowORM.day == day,
                AvailabilityWindowORM.slot_index == slot_index,
            )
        )
        row = result.scalars().first()
        if not row:
            return None
        return AvailabilityWindow(
            workspace_id=row.workspace_id,
            day=row.day,
            slot_index=row.slot_index,
            capacity=Capacity(seats=row.seats),
            version_id=row.version_id,
        )

    async def save(self, window: AvailabilityWindow) -> AvailabilityWindow:
        orm = AvailabilityWindowORM(
            workspace_id=window.workspace_id,
            day=window.day,
            slot_index=window.slot_index,
            seats=window.capacity.seats,
            version_id=window.version_id,
        )
        self.session.add(orm)
        await self.session.commit()
        return window

    async def count_by_window(
        self, workspace_id: UUID, day: str, slot_index: int
    ) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(AvailabilityWindowORM.seats)).where(
                AvailabilityWindowORM.workspace_id == workspace_id,
                AvailabilityWindowORM.day == day,
                AvailabilityWindowORM.slot_index == slot_index,
            )
        )
        return result.scalar() or 0