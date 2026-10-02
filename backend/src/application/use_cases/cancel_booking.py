from uuid import UUID
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.availability_window_repository import AvailabilityWindowRepository
from domain.repositories.quota_repository import QuotaRepository
from domain.entities.booking import Booking, BookingStatus, InvalidStateTransitionError
from domain.entities.quota_period import QuotaPeriod


class CancelBookingUseCase:
    """UC09: Cancelar Reserva (CONFIRMED -> CANCELLED, devolve quota, libera vaga)."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        window_repo: AvailabilityWindowRepository,
        quota_repo: QuotaRepository,
    ):
        self.booking_repo = booking_repo
        self.window_repo = window_repo
        self.quota_repo = quota_repo

    async def execute(self, booking_id: UUID) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found")
        try:
            cancelled = booking.cancel()
        except InvalidStateTransitionError as e:
            raise ValueError(str(e))
        await self.booking_repo.delete_by_booking(booking_id)
        await self.booking_repo.save(cancelled)
        return cancelled