from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from application.use_cases.cancel_booking import (
    BookingAccessDeniedError,
    BookingCancellationError,
    BookingNotFoundError,
    CancelBookingUseCase,
)
from domain.entities.booking import Booking, BookingStatus
from domain.entities.quota_period import QuotaPeriod
from domain.value_objects.time_slot import TimeSlot


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeBookingRepository:
    def __init__(self, booking=None):
        self.booking = booking
        self.saved = []
        self.deleted = []

    async def get_by_id_for_update(self, _booking_id):
        return self.booking

    async def save(self, booking):
        self.saved.append(booking)
        return booking

    async def delete_by_booking(self, booking_id):
        self.deleted.append(booking_id)


class FakeQuotaRepository:
    def __init__(self, quota):
        self.quota = quota
        self.saved = []

    async def get_for_period(self, _cost_center_id, _day):
        return self.quota

    async def save(self, quota):
        self.quota = quota
        self.saved.append(quota)
        return quota


class FakeAuditLogRepository:
    def __init__(self):
        self.entries = []

    async def create(self, **entry):
        self.entries.append(entry)


@pytest.mark.asyncio
async def test_cancel_booking_refunds_quota_and_releases_windows():
    employee_id = uuid4()
    cost_center_id = uuid4()
    start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
    start = start.replace(hour=9, minute=0, second=0, microsecond=0)
    booking = Booking(
        employee_id=employee_id,
        cost_center_id=cost_center_id,
        workspace_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=15)),
    )
    booking_repo = FakeBookingRepository(booking=booking)
    quota_repo = FakeQuotaRepository(
        QuotaPeriod(
            cost_center_id=cost_center_id,
            period_start=start.date().replace(day=1),
            period_end=(start.date().replace(day=28) + timedelta(days=4)).replace(day=1)
            - timedelta(days=1),
            total_hours=Decimal(8),
            consumed_hours=Decimal("0.25"),
        )
    )
    audit_repo = FakeAuditLogRepository()
    use_case = CancelBookingUseCase(booking_repo, quota_repo, audit_repo, FakeUnitOfWork())

    result = await use_case.execute(booking.id, None, is_admin=True)

    assert result.status is BookingStatus.CANCELLED
    assert quota_repo.quota.consumed_hours == Decimal(0)
    assert booking_repo.deleted == [booking.id]
    assert booking_repo.saved == [result]
    assert audit_repo.entries[0]["action"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_booking_rejects_another_employee():
    start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
    start = start.replace(hour=9, minute=0, second=0, microsecond=0)
    booking = Booking(
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        workspace_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=15)),
    )
    booking_repo = FakeBookingRepository(booking=booking)
    quota_repo = FakeQuotaRepository(None)
    use_case = CancelBookingUseCase(
        booking_repo, quota_repo, FakeAuditLogRepository(), FakeUnitOfWork()
    )

    with pytest.raises(BookingAccessDeniedError):
        await use_case.execute(booking.id, uuid4())

    assert booking_repo.saved == []
    assert booking_repo.deleted == []


@pytest.mark.asyncio
async def test_cancel_booking_rejects_late_cancellation():
    start = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=60)
    start = start.replace(second=0, microsecond=0)
    start = start.replace(minute=(start.minute // 15) * 15)
    booking = Booking(
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        workspace_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=15)),
    )
    booking_repo = FakeBookingRepository(booking=booking)
    use_case = CancelBookingUseCase(
        booking_repo,
        FakeQuotaRepository(None),
        FakeAuditLogRepository(),
        FakeUnitOfWork(),
    )

    with pytest.raises(BookingCancellationError, match="2 hours"):
        await use_case.execute(booking.id, booking.employee_id)

    assert booking_repo.saved == []


@pytest.mark.asyncio
async def test_cancel_booking_reports_missing_or_non_cancellable_booking():
    start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
    start = start.replace(hour=9, minute=0, second=0, microsecond=0)
    booking = Booking(
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        workspace_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=15)),
        status=BookingStatus.CANCELLED,
    )
    booking_repo = FakeBookingRepository(booking=booking)
    use_case = CancelBookingUseCase(
        booking_repo,
        FakeQuotaRepository(None),
        FakeAuditLogRepository(),
        FakeUnitOfWork(),
    )

    with pytest.raises(BookingCancellationError, match="current state"):
        await use_case.execute(booking.id, booking.employee_id)

    booking_repo.booking = None
    with pytest.raises(BookingNotFoundError, match="Booking not found"):
        await use_case.execute(booking.id, booking.employee_id)


class FakeEventBus:
    def __init__(self):
        self.published = []

    async def publish(self, event):
        self.published.append(event)


@pytest.mark.asyncio
async def test_cancel_booking_publishes_event_when_bus_provided():
    start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
    start = start.replace(hour=9, minute=0, second=0, microsecond=0)
    booking = Booking(
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        workspace_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=15)),
    )
    booking_repo = FakeBookingRepository(booking=booking)
    quota_repo = FakeQuotaRepository(
        QuotaPeriod(
            cost_center_id=booking.cost_center_id,
            period_start=start.date().replace(day=1),
            period_end=start.date().replace(day=28),
            total_hours=Decimal(8),
            consumed_hours=Decimal("0.25"),
        )
    )
    bus = FakeEventBus()
    use_case = CancelBookingUseCase(
        booking_repo, quota_repo, FakeAuditLogRepository(), FakeUnitOfWork(), event_bus=bus
    )
    result = await use_case.execute(booking.id, booking.employee_id)
    assert result.status is BookingStatus.CANCELLED
    assert len(bus.published) == 1


class BrokenQuota:
    def consume(self, _hours):
        raise ValueError("Invalid refund amount")


@pytest.mark.asyncio
async def test_cancel_booking_wraps_refund_value_error():
    start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
    start = start.replace(hour=9, minute=0, second=0, microsecond=0)
    booking = Booking(
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        workspace_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=15)),
    )
    booking_repo = FakeBookingRepository(booking=booking)
    quota_repo = FakeQuotaRepository(BrokenQuota())
    use_case = CancelBookingUseCase(
        booking_repo, quota_repo, FakeAuditLogRepository(), FakeUnitOfWork()
    )
    with pytest.raises(BookingCancellationError, match="Invalid refund amount"):
        await use_case.execute(booking.id, booking.employee_id)

