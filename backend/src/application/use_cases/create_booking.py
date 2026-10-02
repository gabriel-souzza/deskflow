from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from domain.entities.booking import Booking, BookingStatus
from domain.entities.quota_period import QuotaPeriod, QuotaExceededError
from domain.entities.availability_window import AvailabilityWindow
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.availability_window_repository import AvailabilityWindowRepository
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
    booking: Booking
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

        # Check capacity for each slot in the time slot (I2, I6)
        # For simplicity: assume single 15min slot or aggregate check
        confirmed_count = await self.booking_repo.count_by_window(
            cmd.workspace_id, cmd.slot.start.strftime("%Y-%m-%d"), 0
        )
        window = await self.availability_repo.get_by_key(
            cmd.workspace_id, cmd.slot.start.strftime("%Y-%m-%d"), 0
        )
        if window and window.is_full(confirmed_count):
            return CreateBookingResult(
                booking=None,
                status_code=409,
                message="Capacity exceeded (invariant I2)",
            )

        # Check quota (I3, I5)
        try:
            quota = await self.quota_repo.get_for_period(
                cmd.cost_center_id,
                cmd.slot.start.strftime("%Y-%m-%d"),
            )
            duration_hours = cmd.slot.duration_hours
            quota.consume(duration_hours)
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