from datetime import UTC, datetime, timedelta

from domain.entities.booking import Booking
from domain.repositories.booking_repository import BookingRepository


class ReleaseExpiredBookingsUseCase:
    """UC15: Liberar reservas expiradas (PENDING -> EXPIRED, libera vaga)."""

    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    async def execute(self) -> list[Booking]:
        now = datetime.now(UTC).replace(tzinfo=None)
        expired_bookings = await self.booking_repo.find_pending_expired(
            station_cutoff=now - timedelta(minutes=10),
            meeting_room_cutoff=now - timedelta(minutes=15),
        )

        released = []
        for booking in expired_bookings:
            expired_booking = booking.expire()
            await self.booking_repo.save(expired_booking)
            await self.booking_repo.delete_by_booking(booking.id)
            released.append(expired_booking)

        return released
