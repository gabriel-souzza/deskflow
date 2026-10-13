from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.confirm_booking import (
    BookingNotFoundError,
    CheckInError,
    ConfirmBookingUseCase,
)
from domain.entities.booking import Booking, BookingStatus, InvalidStateTransitionError
from domain.entities.workspace import Workspace, WorkspaceType
from domain.value_objects.time_slot import TimeSlot


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeBookingRepository:
    def __init__(self, booking):
        self.booking = booking
        self.saved = []

    async def get_by_id_for_update(self, _booking_id):
        return self.booking

    async def save(self, booking):
        self.saved.append(booking)
        return booking


class FakeWorkspaceRepository:
    def __init__(self, workspace):
        self.workspace = workspace

    async def get_by_id(self, _workspace_id):
        return self.workspace


class FakeAuditRepository:
    def __init__(self):
        self.entries = []

    async def create(self, **entry):
        self.entries.append(entry)


def make_booking(workspace_type):
    workspace_id = uuid4()
    employee_id = uuid4()
    start = datetime(2026, 10, 10, 9, tzinfo=UTC)
    booking = Booking(
        workspace_id=workspace_id,
        employee_id=employee_id,
        cost_center_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=30)),
    )
    workspace = Workspace(
        id=workspace_id,
        code="W-1",
        floor="1",
        zone="test",
        type=workspace_type,
        capacity=1 if workspace_type is WorkspaceType.STATION else 4,
    )
    return booking, workspace


@pytest.mark.asyncio
async def test_confirm_booking_applies_station_grace_period_and_audits():
    booking, workspace = make_booking(WorkspaceType.STATION)
    repository = FakeBookingRepository(booking)
    audit = FakeAuditRepository()
    use_case = ConfirmBookingUseCase(
        repository, FakeWorkspaceRepository(workspace), audit, FakeUnitOfWork()
    )

    confirmed = await use_case.execute(booking.id, booking.slot.start + timedelta(minutes=10))

    assert confirmed.status is BookingStatus.CONFIRMED
    assert repository.saved == [confirmed]
    assert audit.entries[0]["action"] == "checked_in"


@pytest.mark.asyncio
async def test_confirm_booking_uses_longer_meeting_room_grace_period():
    booking, workspace = make_booking(WorkspaceType.MEETING_ROOM)
    use_case = ConfirmBookingUseCase(
        FakeBookingRepository(booking),
        FakeWorkspaceRepository(workspace),
        FakeAuditRepository(),
        FakeUnitOfWork(),
    )

    confirmed = await use_case.execute(booking.id, booking.slot.start + timedelta(minutes=15))

    assert confirmed.status is BookingStatus.CONFIRMED


@pytest.mark.asyncio
async def test_confirm_booking_rejects_after_grace_period_and_non_pending_state():
    booking, workspace = make_booking(WorkspaceType.STATION)
    repository = FakeBookingRepository(booking)
    use_case = ConfirmBookingUseCase(
        repository, FakeWorkspaceRepository(workspace), FakeAuditRepository(), FakeUnitOfWork()
    )

    with pytest.raises(CheckInError, match="outside"):
        await use_case.execute(booking.id, booking.slot.start + timedelta(minutes=11))

    repository.booking = booking.confirm()
    with pytest.raises(CheckInError, match="pending"):
        await use_case.execute(booking.id, booking.slot.start + timedelta(minutes=1))


@pytest.mark.asyncio
async def test_confirm_booking_reports_missing_booking():
    repository = FakeBookingRepository(None)
    use_case = ConfirmBookingUseCase(
        repository, FakeWorkspaceRepository(None), FakeAuditRepository(), FakeUnitOfWork()
    )

    with pytest.raises(BookingNotFoundError):
        await use_case.execute(uuid4(), datetime.now(UTC))


class FakeEventBus:
    def __init__(self):
        self.published = []

    async def publish(self, event):
        self.published.append(event)


@pytest.mark.asyncio
async def test_confirm_booking_handles_naive_datetimes_and_event_bus():
    workspace_id = uuid4()
    employee_id = uuid4()
    # Naive slot start
    start = datetime(2026, 10, 10, 9, 0)
    booking = Booking(
        workspace_id=workspace_id,
        employee_id=employee_id,
        cost_center_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=30)),
    )
    workspace = Workspace(
        id=workspace_id,
        code="W-1",
        floor="1",
        zone="test",
        type=WorkspaceType.STATION,
        capacity=1,
    )
    bus = FakeEventBus()
    use_case = ConfirmBookingUseCase(
        FakeBookingRepository(booking),
        FakeWorkspaceRepository(workspace),
        FakeAuditRepository(),
        FakeUnitOfWork(),
        event_bus=bus,
    )
    # Naive check-in time
    naive_now = datetime(2026, 10, 10, 9, 5)
    confirmed = await use_case.execute(booking.id, naive_now)
    assert confirmed.status is BookingStatus.CONFIRMED
    assert len(bus.published) == 1


class BookingWithFailingConfirm(Booking):
    def confirm(self):
        raise InvalidStateTransitionError("Forced transition error")


@pytest.mark.asyncio
async def test_confirm_booking_handles_transition_error():
    workspace_id = uuid4()
    start = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
    booking = BookingWithFailingConfirm(
        workspace_id=workspace_id,
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=30)),
        status=BookingStatus.PENDING,
    )
    workspace = Workspace(
        id=workspace_id,
        code="W-1",
        floor="1",
        zone="test",
        type=WorkspaceType.STATION,
        capacity=1,
    )
    use_case = ConfirmBookingUseCase(
        FakeBookingRepository(booking),
        FakeWorkspaceRepository(workspace),
        FakeAuditRepository(),
        FakeUnitOfWork(),
    )
    with pytest.raises(CheckInError, match="Forced transition error"):
        await use_case.execute(booking.id, start)


