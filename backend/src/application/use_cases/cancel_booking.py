from datetime import UTC, datetime, timedelta
from uuid import UUID

from domain.entities.booking import Booking, BookingStatus, InvalidStateTransitionError
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.quota_repository import QuotaRepository
from domain.repositories.unit_of_work import UnitOfWork


class CancelBookingUseCase:
    """UC09: Cancelar Reserva (CONFIRMED -> CANCELLED, devolve quota, libera vaga)."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        quota_repo: QuotaRepository,
        audit_log_repo: AuditLogRepository,
        unit_of_work: UnitOfWork,
    ):
        self.booking_repo = booking_repo
        self.quota_repo = quota_repo
        self.audit_log_repo = audit_log_repo
        self.unit_of_work = unit_of_work

    async def execute(
        self,
        booking_id: UUID,
        requester_id: UUID | None,
        is_admin: bool = False,
    ) -> Booking:
        async with self.unit_of_work.transaction():
            booking = await self.booking_repo.get_by_id_for_update(booking_id)
            if booking is None:
                raise BookingNotFoundError("Booking not found")
            if not is_admin and requester_id != booking.employee_id:
                raise BookingAccessDeniedError("Booking access denied")
            if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
                raise BookingCancellationError("Booking cannot be cancelled in its current state")

            now = datetime.now(UTC)
            booking_start = booking.slot.start
            if booking_start.tzinfo is None:
                booking_start = booking_start.replace(tzinfo=UTC)
            if booking_start - now < timedelta(hours=2):
                raise BookingCancellationError("Cancellation requires at least 2 hours' notice")

            quota = await self.quota_repo.get_for_period(
                booking.cost_center_id, booking.slot.start.date().isoformat()
            )
            try:
                refunded_quota = quota.consume(-booking.duration_hours)
                cancelled = booking.cancel()
            except (ValueError, InvalidStateTransitionError) as exc:
                raise BookingCancellationError(str(exc)) from exc

            await self.quota_repo.save(refunded_quota)
            await self.booking_repo.delete_by_booking(booking_id)
            await self.booking_repo.save(cancelled)
            await self.audit_log_repo.create(
                actor_id=booking.employee_id,
                action="cancelled",
                entity_type="booking",
                entity_id=str(booking_id),
                timestamp=now.replace(tzinfo=None),
                reason="booking cancelled",
            )
            return cancelled


class BookingNotFoundError(Exception):
    pass


class BookingAccessDeniedError(Exception):
    pass


class BookingCancellationError(Exception):
    pass
