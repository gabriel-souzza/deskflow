from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.availability_window import AvailabilityWindow
from domain.entities.booking import BookingStatus
from domain.repositories.availability_window_repository import AvailabilityWindowRepository
from domain.value_objects.capacity import Capacity
from infra.models import AvailabilityWindowORM, BookingORM, BookingWindowORM


class AvailabilityWindowRepositoryPostgres(AvailabilityWindowRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_key(
        self, workspace_id: UUID, day: str, slot_index: int
    ) -> AvailabilityWindow | None:
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
        orm = await self.session.get(
            AvailabilityWindowORM,
            (window.workspace_id, window.day, window.slot_index),
        )
        if orm is None:
            orm = AvailabilityWindowORM(
                workspace_id=window.workspace_id,
                day=window.day,
                slot_index=window.slot_index,
                seats=window.capacity.seats,
                version_id=window.version_id,
            )
            self.session.add(orm)
        else:
            orm.seats = window.capacity.seats
            orm.version_id = window.version_id
        await self.session.flush()
        return window

    async def delete_by_day(self, day: str) -> None:
        await self.session.execute(
            delete(AvailabilityWindowORM).where(AvailabilityWindowORM.day == day)
        )

    async def count_by_window(self, workspace_id: UUID, day: str, slot_index: int) -> int:
        result = await self.session.execute(
            select(func.count(BookingWindowORM.booking_id))
            .join(BookingORM, BookingORM.id == BookingWindowORM.booking_id)
            .where(
                BookingWindowORM.workspace_id == workspace_id,
                BookingWindowORM.day == day,
                BookingWindowORM.slot_index == slot_index,
                BookingORM.status.in_((BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value)),
            )
        )
        return result.scalar() or 0
