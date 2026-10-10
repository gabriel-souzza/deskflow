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


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class BookingRepositoryPostgres(BookingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self.session.execute(select(BookingORM).where(BookingORM.id == booking_id))
        row = result.scalars().first()
        return self._to_entity(row)

    async def get_by_id_for_update(self, booking_id: UUID) -> Booking | None:
        result = await self.session.execute(
            select(BookingORM).where(BookingORM.id == booking_id).with_for_update()
        )
        return self._to_entity(result.scalars().first())

    @staticmethod
    def _to_entity(row: BookingORM | None) -> Booking | None:
        if not row:
            return None
        return Booking(
            id=row.id,
            workspace_id=row.workspace_id,
            employee_id=row.employee_id,
            cost_center_id=row.cost_center_id,
            slot=TimeSlot(start=_aware_utc(row.slot_start), end=_aware_utc(row.slot_end)),
            status=BookingStatus(row.status),
            created_at=_aware_utc(row.created_at),
            modified_at=_aware_utc(row.modified_at),
        )

    async def save(self, booking: Booking) -> Booking:
        result = await self.session.execute(select(BookingORM).where(BookingORM.id == booking.id))
        orm = result.scalars().first()
        is_new = orm is None
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
        if is_new:
            await self.session.flush()
            day = booking.slot.start.date().isoformat()
            self.session.add_all(
                BookingWindowORM(
                    booking_id=booking.id,
                    workspace_id=booking.workspace_id,
                    day=day,
                    slot_index=(slot_start.hour * 60 + slot_start.minute - 8 * 60) // 15,
                )
                for slot_start in booking.slot.slots()
            )
        return booking

    async def delete_by_booking(self, booking_id: UUID) -> None:
        await self.session.execute(
            delete(BookingWindowORM).where(BookingWindowORM.booking_id == booking_id)
        )

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
                slot=TimeSlot(start=_aware_utc(row.slot_start), end=_aware_utc(row.slot_end)),
                status=BookingStatus(row.status),
                created_at=_aware_utc(row.created_at),
                modified_at=_aware_utc(row.modified_at),
            )
            for row in result.scalars().all()
        ]

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

    async def list_between(self, start: datetime, end: datetime) -> list[Booking]:
        result = await self.session.execute(
            select(BookingORM)
            .where(BookingORM.slot_start < _naive_utc(end), BookingORM.slot_end > _naive_utc(start))
            .order_by(BookingORM.slot_start, BookingORM.id)
        )
        return [self._to_entity(row) for row in result.scalars().all()]
