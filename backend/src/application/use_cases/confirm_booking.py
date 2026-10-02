from uuid import UUID
from domain.repositories.booking_repository import BookingRepository
from domain.entities.booking import Booking, BookingStatus, InvalidStateTransitionError


class ConfirmBookingUseCase:
    """UC06: Check-in via QR Code (PENDING -> CONFIRMED, I4)."""

    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    async def execute(self, booking_id: UUID, token: str) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found")
        try:
            confirmed = booking.confirm()
        except InvalidStateTransitionError as e:
            raise ValueError(str(e))
        await self.booking_repo.save(confirmed)
        return confirmed