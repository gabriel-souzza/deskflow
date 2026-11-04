from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from domain.entities.booking import Booking, BookingStatus
from domain.entities.quota_period import QuotaExceededError
from domain.entities.waitlist import Waitlist
from domain.entities.workspace import WorkspaceType
from domain.events.event_bus import EventBus
from domain.events.events import BookingCreated, QuotaConsumed
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.repositories.availability_window_repository import (
    AvailabilityWindowRepository,
    RepositoryConflictError,
)
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.employee_repository import EmployeeRepository
from domain.repositories.quota_repository import QuotaRepository
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.waitlist_repository import WaitlistRepository
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


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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
        window_repo: AvailabilityWindowRepository | None = None,
        event_bus: EventBus | None = None,
        waitlist_repo: WaitlistRepository | None = None,
    ):
        self.booking_repo = booking_repo
        self.workspace_repo = workspace_repo
        self.employee_repo = employee_repo
        self.quota_repo = quota_repo
        self.audit_log_repo = audit_log_repo
        self.unit_of_work = unit_of_work
        self.window_repo = window_repo
        self.event_bus = event_bus
        self.waitlist_repo = waitlist_repo

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

            active_holds: list[Waitlist] = []
            user_holds: list[Waitlist] = []
            if self.waitlist_repo is not None:
                now = datetime.now(UTC)
                all_entries = await self.waitlist_repo.list_all_by_workspace(cmd.workspace_id)
                for entry in all_entries:
                    if entry.notified_at is not None:
                        notified_utc = _to_utc(entry.notified_at)
                        if (now - notified_utc) < timedelta(minutes=5):
                            active_holds.append(entry)
                            if entry.employee_id == cmd.employee_id:
                                user_holds.append(entry)

            day_key = day.isoformat()
            slot_indices = []
            for slot_start in cmd.slot.slots():
                slot_index = (slot_start.hour * 60 + slot_start.minute - 8 * 60) // 15
                slot_indices.append(slot_index)
                occupied = await self.booking_repo.count_by_window(
                    cmd.workspace_id, day_key, slot_index
                )
                if occupied >= workspace.capacity:
                    return CreateBookingResult(None, 409, "Workspace capacity is unavailable")

                if self.waitlist_repo is not None:
                    slot_end = slot_start + timedelta(minutes=15)
                    s_start = _to_utc(slot_start)
                    s_end = _to_utc(slot_end)
                    others_holding_this_slot = [
                        entry
                        for entry in active_holds
                        if entry.employee_id != cmd.employee_id
                        and not (
                            _to_utc(entry.desired_slot_end) <= s_start
                            or _to_utc(entry.desired_slot_start) >= s_end
                        )
                    ]
                    if (workspace.capacity - occupied) <= len(others_holding_this_slot):
                        return CreateBookingResult(
                            None, 409, "Slot is reserved for a waitlist notification"
                        )

            try:
                quota = await self.quota_repo.get_for_period(cmd.cost_center_id, day_key)
                updated_quota = quota.consume(cmd.slot.duration_hours)
            except LookupError as exc:
                return CreateBookingResult(None, 404, str(exc))
            except QuotaExceededError as exc:
                return CreateBookingResult(None, 402, str(exc))

            # Invariant I6: update version_id on availability windows if window_repo provided
            if self.window_repo is not None:
                for slot_index in slot_indices:
                    win = (
                        await self.window_repo.get_or_create(
                            cmd.workspace_id, day_key, slot_index, default_seats=workspace.capacity
                        )
                        if hasattr(self.window_repo, "get_or_create")
                        else await self.window_repo.get_by_key(cmd.workspace_id, day_key, slot_index)
                    )
                    if win is not None:
                        updated_win = win.increment_version()
                        try:
                            await self.window_repo.save(updated_win, expected_version=win.version_id)
                        except RepositoryConflictError as exc:
                            return CreateBookingResult(None, 409, str(exc))

            booking = Booking(
                workspace_id=cmd.workspace_id,
                employee_id=cmd.employee_id,
                cost_center_id=cmd.cost_center_id,
                slot=cmd.slot,
                status=BookingStatus.PENDING,
            )
            await self.quota_repo.save(updated_quota)
            await self.booking_repo.save(booking)
            if self.waitlist_repo is not None:
                deleted_ids: set[UUID] = set()
                for hold in user_holds:
                    await self.waitlist_repo.delete(hold.id)
                    deleted_ids.add(hold.id)
                user_entry = await self.waitlist_repo.get_by_workspace_employee(
                    cmd.workspace_id, cmd.employee_id
                )
                if user_entry is not None and user_entry.id not in deleted_ids:
                    e_start = _to_utc(user_entry.desired_slot_start)
                    e_end = _to_utc(user_entry.desired_slot_end)
                    s_start = _to_utc(cmd.slot.start)
                    s_end = _to_utc(cmd.slot.end)
                    if not (e_end <= s_start or e_start >= s_end):
                        await self.waitlist_repo.delete(user_entry.id)
            await self.audit_log_repo.create(
                actor_id=employee.id,
                action="created",
                entity_type="booking",
                entity_id=str(booking.id),
                timestamp=datetime.now(UTC).replace(tzinfo=None),
                reason="booking created",
            )

        if self.event_bus is not None:
            await self.event_bus.publish(
                QuotaConsumed(
                    cost_center_id=cmd.cost_center_id,
                    period_start=quota.period_start,
                    total_hours=updated_quota.total_hours,
                    consumed_hours=updated_quota.consumed_hours,
                    delta_hours=cmd.slot.duration_hours,
                )
            )
            await self.event_bus.publish(
                BookingCreated(
                    booking_id=booking.id,
                    workspace_id=cmd.workspace_id,
                    employee_id=cmd.employee_id,
                    cost_center_id=cmd.cost_center_id,
                    slot=cmd.slot,
                )
            )

        return CreateBookingResult(
            booking=booking,
            status_code=201,
            message="Booking created (PENDING)",
            workspace_type=workspace.type,
        )
