from uuid import UUID
from domain.repositories.booking_repository import BookingRepository
from domain.entities.booking import Booking, BookingStatus


class ReleaseExpiredBookingsUseCase:
    """UC15: Liberar reservas expiradas (PENDING -> EXPIRED, libera vaga)."""

    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    async def execute(self) -> list[Booking]:
        # Em produção: buscar todos PENDING que excederam 10min
        # Para esta implementação: placeholder
        return []