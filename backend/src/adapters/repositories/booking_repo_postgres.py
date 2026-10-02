from typing import Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.repositories.booking_repository import BookingRepository
from domain.entities.booking import Booking, BookingStatus
from domain.value_objects.time_slot import TimeSlot
from infra.models import BookingORM, BookingWindowORM


class BookingRepositoryPostgres(BookingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, booking_id: UUID) -> Optional[Booking]:
        result = await self.session.execute(
            select(BookingORM).where(BookingORM.id == booking_id)
        )
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
        orm = BookingORM(
            id=booking.id,
            workspace_id=booking.workspace_id,
            employee_id=booking.employee_id,
            cost_center_id=booking.cost_center_id,
            slot_start=booking.slot.start,
            slot_end=booking.slot.end,
            status=booking.status.value,
            created_at=booking.created_at,
            modified_at=booking.modified_at,
        )
        self.session.add(orm)
        await self.session.commit()
        return booking

    async def delete_by_booking(self, booking_id: UUID) -> None:
        await self.session.execute(
            select(BookingWindowORM).where(BookingWindowORM.booking_id == booking_id)
        )
        # Em produção: DELETE FROM booking_windows WHERE booking_id = ...

    async def count_by_window(
        self, workspace_id: UUID, day: str, slot_index: int
    ) -> int:
        # Conta booking_windows confirmados para a janela
        result = await self.session.execute(
            select(func.count(BookingWindowORM.booking_id))
            .where(
                BookingWindowORM.workspace_id == workspace_id,
                BookingWindowORM.day == day,
                BookingWindowORM.slot_index == slot_index,
            )
        )
        return result.scalar() or 0