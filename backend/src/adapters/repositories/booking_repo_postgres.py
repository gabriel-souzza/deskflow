from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.booking import Booking, BookingStatus
from domain.repositories.booking_repository import BookingRepository
from domain.value_objects.time_slot import TimeSlot
from infra.models import BookingORM, BookingWindowORM, WorkspaceORM


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


class BookingRepositoryPostgres(BookingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self.session.execute(select(BookingORM).where(BookingORM.id == booking_id))
        row = result.scalars().first()
        if not row:
            return None
        return Booking(
            id=row.id,
            workspace_id=row.workspace_id,
            employee_id=row.employee_id,
            cost_center_id=row.cost_center_id,
            slot=TimeSlot(start=row.slot_start, end=row.slot_end),
            status=BookingStatus(row.status),
            created_at=row.created_at,
            modified_at=row.modified_at,
        )

    async def save(self, booking: Booking) -> Booking:
        result = await self.session.execute(select(BookingORM).where(BookingORM.id == booking.id))
        orm = result.scalars().first()
        if orm is None:
            orm = BookingORM(id=booking.id)
            self.session.add(orm)

        orm.workspace_id = booking.workspace_id
        orm.employee_id = booking.employee_id
        orm.cost_center_id = booking.cost_center_id
        orm.slot_start = _naive_utc(booking.slot.start)
        orm.slot_end = _naive_utc(booking.slot.end)
        orm.status = booking.status.value
        orm.created_at = _naive_utc(booking.created_at)
        orm.modified_at = _naive_utc(booking.modified_at)
        await self.session.commit()
        return booking

    async def delete_by_booking(self, booking_id: UUID) -> None:
        await self.session.execute(
            delete(BookingWindowORM).where(BookingWindowORM.booking_id == booking_id)
        )
        await self.session.commit()

    async def find_pending_expired(
        self,
        station_cutoff: datetime,
        meeting_room_cutoff: datetime,
    ) -> list[Booking]:
        result = await self.session.execute(
            select(BookingORM)
            .join(WorkspaceORM, BookingORM.workspace_id == WorkspaceORM.id)
            .where(
                BookingORM.status == BookingStatus.PENDING.value,
                or_(
                    (WorkspaceORM.type == "estacao") & (BookingORM.slot_start <= station_cutoff),
                    (WorkspaceORM.type == "sala") & (BookingORM.slot_start <= meeting_room_cutoff),
                ),
            )
        )
        return [
            Booking(
                id=row.id,
                workspace_id=row.workspace_id,
                employee_id=row.employee_id,
                cost_center_id=row.cost_center_id,
                slot=TimeSlot(start=row.slot_start, end=row.slot_end),
                status=BookingStatus(row.status),
                created_at=row.created_at,
                modified_at=row.modified_at,
            )
            for row in result.scalars().all()
        ]

    async def count_by_window(self, workspace_id: UUID, day: str, slot_index: int) -> int:
        # Conta booking_windows confirmados para a janela
        result = await self.session.execute(
            select(func.count(BookingWindowORM.booking_id)).where(
                BookingWindowORM.workspace_id == workspace_id,
                BookingWindowORM.day == day,
                BookingWindowORM.slot_index == slot_index,
            )
        )
        return result.scalar() or 0
