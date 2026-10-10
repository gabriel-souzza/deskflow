from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from application.use_cases.create_booking import CreateBookingCommand, CreateBookingUseCase
from domain.entities.booking import BookingStatus
from domain.entities.employee import Employee
from domain.entities.quota_period import QuotaPeriod
from domain.entities.workspace import Workspace, WorkspaceType
from domain.value_objects.time_slot import TimeSlot


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeBookingRepository:
    def __init__(self, occupied=0, booking=None):
        self.occupied = occupied
        self.booking = booking
        self.saved = []
        self.deleted = []

    async def count_by_window(self, _workspace_id, _day, _slot_index):
        return self.occupied

    async def save(self, booking):
        self.saved.append(booking)
        return booking

    async def get_by_id_for_update(self, _booking_id):
        return self.booking

    async def delete_by_booking(self, booking_id):
        self.deleted.append(booking_id)


class FakeWorkspaceRepository:
    def __init__(self, workspace):
        self.workspace = workspace

    async def get_for_booking(self, _workspace_id):
        return self.workspace


class FakeEmployeeRepository:
    def __init__(self, employee):
        self.employee = employee

    async def get_by_id(self, _employee_id):
        return self.employee


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


def build_booking_dependencies(*, occupied=0, total_hours=Decimal(8), eligible=True):
    workspace_id = uuid4()
    employee_id = uuid4()
    cost_center_id = uuid4()
    slot_start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=3)
    slot_start = slot_start.replace(hour=9, minute=0, second=0, microsecond=0)
    slot = TimeSlot(slot_start, slot_start + timedelta(minutes=30))
    booking_repo = FakeBookingRepository(occupied=occupied)
    workspace_repo = FakeWorkspaceRepository(
        Workspace(
            id=workspace_id,
            code="A-1",
            floor="1",
            zone="open",
            type=WorkspaceType.STATION,
            capacity=1,
        )
    )
    employee_repo = FakeEmployeeRepository(
        Employee(
            id=employee_id,
            name="Employee",
            email="employee@example.test",
            cost_center_id=cost_center_id,
            is_eligible_for_booking=eligible,
        )
    )
    quota_repo = FakeQuotaRepository(
        QuotaPeriod(
            cost_center_id=cost_center_id,
            period_start=slot_start.date().replace(day=1),
            period_end=(slot_start.date().replace(day=28) + timedelta(days=4)).replace(day=1)
            - timedelta(days=1),
            total_hours=total_hours,
        )
    )
    audit_repo = FakeAuditLogRepository()
    use_case = CreateBookingUseCase(
        booking_repo,
        workspace_repo,
        employee_repo,
        quota_repo,
        audit_repo,
        FakeUnitOfWork(),
    )
    command = CreateBookingCommand(workspace_id, employee_id, cost_center_id, slot)
    return use_case, command, booking_repo, quota_repo, audit_repo


@pytest.mark.asyncio
async def test_create_booking_consumes_quota_and_persists_pending_booking():
    use_case, command, booking_repo, quota_repo, audit_repo = build_booking_dependencies()

    result = await use_case.execute(command)

    assert result.status_code == 201
    assert result.booking is not None
    assert result.booking.status is BookingStatus.PENDING
    assert quota_repo.quota.consumed_hours == Decimal("0.5")
    assert booking_repo.saved == [result.booking]
    assert audit_repo.entries[0]["entity_id"] == str(result.booking.id)


@pytest.mark.asyncio
async def test_create_booking_rejects_full_capacity_without_consuming_quota():
    use_case, command, booking_repo, quota_repo, audit_repo = build_booking_dependencies(occupied=1)

    result = await use_case.execute(command)

    assert result.status_code == 409
    assert booking_repo.saved == []
    assert quota_repo.saved == []
    assert audit_repo.entries == []


@pytest.mark.asyncio
async def test_create_booking_rejects_ineligible_employee():
    use_case, command, booking_repo, quota_repo, _audit_repo = build_booking_dependencies(
        eligible=False
    )

    result = await use_case.execute(command)

    assert result.status_code == 403
    assert booking_repo.saved == []
    assert quota_repo.saved == []


@pytest.mark.asyncio
async def test_create_booking_rejects_insufficient_quota():
    use_case, command, booking_repo, quota_repo, audit_repo = build_booking_dependencies(
        total_hours=Decimal("0.25")
    )

    result = await use_case.execute(command)

    assert result.status_code == 402
    assert booking_repo.saved == []
    assert quota_repo.saved == []
    assert audit_repo.entries == []


@pytest.mark.asyncio
async def test_create_booking_reports_missing_workspace_or_employee():
    use_case, command, _booking_repo, _quota_repo, _audit_repo = build_booking_dependencies()
    use_case.workspace_repo.workspace = None

    missing_workspace = await use_case.execute(command)
    assert missing_workspace.status_code == 404

    use_case, command, _booking_repo, _quota_repo, _audit_repo = build_booking_dependencies()
    use_case.employee_repo.employee = None

    missing_employee = await use_case.execute(command)
    assert missing_employee.status_code == 404


@pytest.mark.asyncio
async def test_create_booking_rejects_mismatched_cost_center_and_outside_hours():
    use_case, command, _booking_repo, _quota_repo, _audit_repo = build_booking_dependencies()
    wrong_center = replace(command, cost_center_id=uuid4())

    mismatch = await use_case.execute(wrong_center)
    assert mismatch.status_code == 422

    outside_start = command.slot.start.replace(hour=7, minute=45)
    outside_slot = TimeSlot(outside_start, outside_start + timedelta(minutes=15))
    outside_hours = await use_case.execute(replace(command, slot=outside_slot))
    assert outside_hours.status_code == 409

