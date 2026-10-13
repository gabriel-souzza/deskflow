from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from application.use_cases.generate_report import GenerateReportUseCase
from domain.entities.booking import Booking, BookingStatus
from domain.entities.workspace import Workspace, WorkspaceType
from domain.value_objects.time_slot import TimeSlot


class FakeBookingRepository:
    def __init__(self, bookings):
        self.bookings = bookings

    async def list_between(self, start, end):
        return [
            booking
            for booking in self.bookings
            if booking.slot.start < end and booking.slot.end > start
        ]


class FakeWorkspaceRepository:
    def __init__(self, workspaces):
        self.workspaces = workspaces

    async def list_all_active(self):
        return self.workspaces


def make_workspace(floor, zone, capacity):
    return Workspace(
        id=uuid4(),
        code=f"{floor}-{uuid4()}",
        floor=floor,
        zone=zone,
        type=WorkspaceType.STATION if capacity == 1 else WorkspaceType.MEETING_ROOM,
        capacity=capacity,
    )


@pytest.mark.asyncio
async def test_report_aggregates_utilization_and_cost_center_hours():
    workspace = make_workspace("2", "open", 2)
    employee_id = uuid4()
    cost_center_id = uuid4()
    start = datetime.combine(date(2026, 10, 12), time(9), tzinfo=UTC)
    bookings = [
        Booking(
            workspace_id=workspace.id,
            employee_id=employee_id,
            cost_center_id=cost_center_id,
            slot=TimeSlot(start, start + timedelta(minutes=30)),
            status=BookingStatus.CONFIRMED,
        ),
        Booking(
            workspace_id=workspace.id,
            employee_id=uuid4(),
            cost_center_id=cost_center_id,
            slot=TimeSlot(start + timedelta(hours=1), start + timedelta(hours=1, minutes=30)),
            status=BookingStatus.PENDING,
        ),
    ]
    use_case = GenerateReportUseCase(
        FakeBookingRepository(bookings), FakeWorkspaceRepository([workspace])
    )

    report = await use_case.execute(date(2026, 10, 12), date(2026, 10, 12))

    assert report["summary"]["bookings_confirmed"] == 1
    assert report["summary"]["occupied_slot_seats"] == 2
    assert report["summary"]["total_slot_seats"] == 80
    assert report["summary"]["occupancy_rate"] == 0.025
    assert report["cost_center_hours"][str(cost_center_id)] == Decimal("1.0")
    assert report["by_floor"]["2"]["occupied_slot_seats"] == 2
    assert len(report["bookings"]) == 2


@pytest.mark.asyncio
async def test_report_rejects_reversed_period():
    use_case = GenerateReportUseCase(FakeBookingRepository([]), FakeWorkspaceRepository([]))

    with pytest.raises(ValueError, match="end date"):
        await use_case.execute(date(2026, 10, 13), date(2026, 10, 12))


@pytest.mark.asyncio
async def test_report_skips_booking_with_missing_workspace():
    start = datetime.combine(date(2026, 10, 12), time(9), tzinfo=UTC)
    booking_orphan = Booking(
        workspace_id=uuid4(),  # not in repo
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        slot=TimeSlot(start, start + timedelta(minutes=30)),
        status=BookingStatus.CONFIRMED,
    )
    use_case = GenerateReportUseCase(
        FakeBookingRepository([booking_orphan]), FakeWorkspaceRepository([])
    )
    report = await use_case.execute(date(2026, 10, 12), date(2026, 10, 12))
    assert len(report["bookings"]) == 0

