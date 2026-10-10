from datetime import UTC, datetime, timedelta
from uuid import UUID

from domain.entities.booking import Booking, BookingStatus, InvalidStateTransitionError
from domain.entities.workspace import WorkspaceType
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.workspace_repository import WorkspaceRepository


class ConfirmBookingUseCase:
    """UC06: Check-in via QR Code (PENDING -> CONFIRMED, I4)."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        workspace_repo: WorkspaceRepository,
        audit_log_repo: AuditLogRepository,
        unit_of_work: UnitOfWork,
    ):
        self.booking_repo = booking_repo
        self.workspace_repo = workspace_repo
        self.audit_log_repo = audit_log_repo
        self.unit_of_work = unit_of_work

    async def execute(self, booking_id: UUID, now: datetime) -> Booking:
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        else:
            now = now.astimezone(UTC)

        async with self.unit_of_work.transaction():
            booking = await self.booking_repo.get_by_id_for_update(booking_id)
            if booking is None:
                raise BookingNotFoundError("Booking not found")
            if booking.status is not BookingStatus.PENDING:
                raise CheckInError("Only pending bookings can be checked in")

            workspace = await self.workspace_repo.get_by_id(booking.workspace_id)
            grace_minutes = 15 if workspace and workspace.type is WorkspaceType.MEETING_ROOM else 10
            start = booking.slot.start
            if start.tzinfo is None:
                start = start.replace(tzinfo=UTC)
            if now < start or now > start + timedelta(minutes=grace_minutes):
                raise CheckInError("Check-in is outside the allowed time window")

            try:
                confirmed = booking.confirm()
            except InvalidStateTransitionError as exc:
                raise CheckInError(str(exc)) from exc
            await self.booking_repo.save(confirmed)
            await self.audit_log_repo.create(
                actor_id=booking.employee_id,
                action="checked_in",
                entity_type="booking",
                entity_id=str(booking.id),
                timestamp=now.replace(tzinfo=None),
                reason="QR check-in",
            )
            return confirmed


class BookingNotFoundError(Exception):
    pass


class CheckInError(Exception):
    pass
