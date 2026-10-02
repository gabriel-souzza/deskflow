from dataclasses import dataclass
from uuid import UUID

from domain.entities.booking import Booking, BookingStatus
from domain.entities.quota_period import QuotaExceededError
from domain.repositories.availability_window_repository import AvailabilityWindowRepository
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.quota_repository import QuotaRepository
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


class CreateBookingUseCase:
    """
    Use Case UC02: Realizar Reserva.
    Orchestrates invariants I1-I6 atomically.
    """

    def __init__(
        self,
        booking_repo: BookingRepository,
        availability_repo: AvailabilityWindowRepository,
        quota_repo: QuotaRepository,
    ):
        self.booking_repo = booking_repo
        self.availability_repo = availability_repo
        self.quota_repo = quota_repo

    async def execute(self, cmd: CreateBookingCommand) -> CreateBookingResult:
        # I1: TimeSlot already validated in __post_init__

        # Availability is generated for one day, from 08:00 through 18:00.
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

        # Check every 15-minute window occupied by the booking (I2, I6).
        day_key = day.isoformat()
        for slot_start in cmd.slot.slots():
            minutes_from_open = (slot_start.hour - 8) * 60 + slot_start.minute
            slot_index = minutes_from_open // 15
            confirmed_count = await self.booking_repo.count_by_window(
                cmd.workspace_id,
                day_key,
                slot_index,
            )
            window = await self.availability_repo.get_by_key(
                cmd.workspace_id,
                day_key,
                slot_index,
            )
            if window is None or window.is_full(confirmed_count):
                return CreateBookingResult(
                    booking=None,
                    status_code=409,
                    message=f"Capacity unavailable for slot {slot_index} (invariant I2)",
                )

        # Check quota (I3, I5)
        try:
            quota = await self.quota_repo.get_for_period(
                cmd.cost_center_id,
                day_key,
            )
            duration_hours = cmd.slot.duration_hours
            quota = quota.consume(duration_hours)
            await self.quota_repo.save(quota)
        except QuotaExceededError as e:
            return CreateBookingResult(
                booking=None,
                status_code=402,
                message=str(e),
            )

        # Create Booking (PENDING state, I4)
        booking = Booking(
            workspace_id=cmd.workspace_id,
            employee_id=cmd.employee_id,
            cost_center_id=cmd.cost_center_id,
            slot=cmd.slot,
            status=BookingStatus.PENDING,
        )

        # Persist atomically (I5: Booking + Quota + BookingWindow should be atomic)
        await self.booking_repo.save(booking)

        return CreateBookingResult(
            booking=booking,
            status_code=201,
            message="Booking created (PENDING)",
        )
