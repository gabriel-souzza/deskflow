from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from domain.entities.booking import Booking, BookingStatus
from domain.entities.quota_period import QuotaExceededError
from domain.entities.workspace import WorkspaceType
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.employee_repository import EmployeeRepository
from domain.repositories.quota_repository import QuotaRepository
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.workspace_repository import WorkspaceRepository
from domain.value_objects.time_slot import TimeSlot


@dataclass(frozen=True)
class CreateBookingCommand:
    workspace_id: UUID
    employee_id: UUID
    cost_center_id: UUID
    slot: TimeSlot


@dataclass(frozen=True)
class CreateBookingResult:
    booking: Booking | None
    status_code: int
    message: str
    workspace_type: WorkspaceType | None = None


class CreateBookingUseCase:
    """
    Use Case UC02: Realizar Reserva.
    Orchestrates invariants I1-I6 atomically.
    """

    def __init__(
        self,
        booking_repo: BookingRepository,
        workspace_repo: WorkspaceRepository,
        employee_repo: EmployeeRepository,
        quota_repo: QuotaRepository,
        audit_log_repo: AuditLogRepository,
        unit_of_work: UnitOfWork,
    ):
        self.booking_repo = booking_repo
        self.workspace_repo = workspace_repo
        self.employee_repo = employee_repo
        self.quota_repo = quota_repo
        self.audit_log_repo = audit_log_repo
        self.unit_of_work = unit_of_work

    async def execute(self, cmd: CreateBookingCommand) -> CreateBookingResult:
        day = cmd.slot.start.date()
        if (
            day != cmd.slot.end.date()
            or cmd.slot.start.hour * 60 + cmd.slot.start.minute < 8 * 60
            or cmd.slot.end.hour * 60 + cmd.slot.end.minute > 18 * 60
        ):
            return CreateBookingResult(
                booking=None,
                status_code=409,
                message="The requested time is outside the daily availability window",
            )

        async with self.unit_of_work.transaction():
            workspace = await self.workspace_repo.get_for_booking(cmd.workspace_id)
            if workspace is None:
                return CreateBookingResult(
                    booking=None,
                    status_code=404,
                    message="Workspace not found",
                )
            employee = await self.employee_repo.get_by_id(cmd.employee_id)
            if employee is None:
                return CreateBookingResult(None, 404, "Employee not found")
            if employee.cost_center_id != cmd.cost_center_id:
                return CreateBookingResult(
                    None, 422, "Employee does not belong to this cost center"
                )
            if not employee.check_eligibility(day):
                return CreateBookingResult(None, 403, "Employee is not eligible to book")

            day_key = day.isoformat()
            for slot_start in cmd.slot.slots():
                slot_index = (slot_start.hour * 60 + slot_start.minute - 8 * 60) // 15
                occupied = await self.booking_repo.count_by_window(
                    cmd.workspace_id, day_key, slot_index
                )
                if occupied >= workspace.capacity:
                    return CreateBookingResult(None, 409, "Workspace capacity is unavailable")

            try:
                quota = await self.quota_repo.get_for_period(cmd.cost_center_id, day_key)
                updated_quota = quota.consume(cmd.slot.duration_hours)
            except LookupError as exc:
                return CreateBookingResult(None, 404, str(exc))
            except QuotaExceededError as exc:
                return CreateBookingResult(None, 402, str(exc))

            booking = Booking(
                workspace_id=cmd.workspace_id,
                employee_id=cmd.employee_id,
                cost_center_id=cmd.cost_center_id,
                slot=cmd.slot,
                status=BookingStatus.PENDING,
            )
            await self.quota_repo.save(updated_quota)
            await self.booking_repo.save(booking)
            await self.audit_log_repo.create(
                actor_id=employee.id,
                action="created",
                entity_type="booking",
                entity_id=str(booking.id),
                timestamp=datetime.now(UTC).replace(tzinfo=None),
                reason="booking created",
            )
            return CreateBookingResult(
                booking=booking,
                status_code=201,
                message="Booking created (PENDING)",
                workspace_type=workspace.type,
            )
