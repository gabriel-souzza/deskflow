from datetime import UTC, datetime, timedelta

from domain.entities.booking import Booking
from domain.events.event_bus import EventBus
from domain.events.events import BookingExpired
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.unit_of_work import UnitOfWork


class ReleaseExpiredBookingsUseCase:
    """UC15: Liberar reservas expiradas (PENDING -> EXPIRED, libera vaga)."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        unit_of_work: UnitOfWork | None = None,
        event_bus: EventBus | None = None,
    ):
        self.booking_repo = booking_repo
        self.unit_of_work = unit_of_work
        self.event_bus = event_bus

    async def execute(self) -> list[Booking]:
        now = datetime.now(UTC).replace(tzinfo=None)
        expired_bookings = await self.booking_repo.find_pending_expired(
            station_cutoff=now - timedelta(minutes=10),
            meeting_room_cutoff=now - timedelta(minutes=15),
        )

        released = []

        async def _process():
            for booking in expired_bookings:
                expired_booking = booking.expire()
                await self.booking_repo.save(expired_booking)
                await self.booking_repo.delete_by_booking(booking.id)
                released.append(expired_booking)

        if self.unit_of_work is not None:
            async with self.unit_of_work.transaction():
                await _process()
        else:
            await _process()

        if self.event_bus is not None:
            for expired_booking in released:
                await self.event_bus.publish(
                    BookingExpired(
                        booking_id=expired_booking.id,
                        workspace_id=expired_booking.workspace_id,
                        employee_id=expired_booking.employee_id,
                        slot=expired_booking.slot,
                    )
                )

        return released
