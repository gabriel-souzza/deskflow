from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.join_waitlist import JoinWaitlistUseCase
from domain.entities.employee import Employee
from domain.entities.waitlist import Waitlist
from domain.entities.workspace import Workspace, WorkspaceType
from domain.value_objects.time_slot import TimeSlot


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeWaitlistRepository:
    def __init__(self, entries=None):
        self.entries = entries or []

    async def get_by_workspace_employee(self, workspace_id, employee_id):
        return next(
            (
                entry
                for entry in self.entries
                if entry.workspace_id == workspace_id and entry.employee_id == employee_id
            ),
            None,
        )

    async def create(self, workspace_id, employee_id, desired_slot):
        entry = Waitlist(
            workspace_id=workspace_id,
            employee_id=employee_id,
            desired_slot_start=desired_slot.start,
            desired_slot_end=desired_slot.end,
        )
        self.entries.append(entry)
        return entry


class FakeWorkspaceRepository:
    def __init__(self, workspace):
        self.workspace = workspace

    async def get_by_id(self, workspace_id):
        return self.workspace if self.workspace and self.workspace.id == workspace_id else None


class FakeEmployeeRepository:
    def __init__(self, employee):
        self.employee = employee

    async def get_by_id(self, employee_id):
        return self.employee if self.employee and self.employee.id == employee_id else None


class FakeBookingRepository:
    def __init__(self, count=1):
        self.count = count

    async def count_by_window(self, _workspace_id, _day, _slot_index):
        return self.count


@pytest.mark.asyncio
async def test_join_waitlist_is_idempotent_for_existing_employee_workspace_pair():
    workspace_id = uuid4()
    employee_id = uuid4()
    cost_center_id = uuid4()
    slot_start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=2)
    slot_start = slot_start.replace(hour=9, minute=0, second=0, microsecond=0)
    slot = TimeSlot(slot_start, slot_start + timedelta(minutes=15))
    employee = Employee(
        id=employee_id,
        name="Employee",
        email="employee@example.test",
        cost_center_id=cost_center_id,
        is_eligible_for_booking=True,
    )
    workspace = Workspace(
        id=workspace_id,
        code="W-1",
        floor="1",
        zone="test",
        type=WorkspaceType.STATION,
        capacity=1,
    )
    repository = FakeWaitlistRepository([])
    use_case = JoinWaitlistUseCase(
        repository,
        FakeWorkspaceRepository(workspace),
        FakeEmployeeRepository(employee),
        FakeBookingRepository(count=1),
        FakeUnitOfWork(),
    )

    first = await use_case.execute(workspace_id, employee_id, slot)
    second = await use_case.execute(workspace_id, employee_id, slot)

    assert first == second
    assert len(repository.entries) == 1


@pytest.mark.asyncio
async def test_join_waitlist_fails_when_workspace_not_found_or_not_eligible():
    workspace_id = uuid4()
    employee_id = uuid4()
    slot_start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=2)
    slot_start = slot_start.replace(hour=9, minute=0, second=0, microsecond=0)
    slot = TimeSlot(slot_start, slot_start + timedelta(minutes=15))

    employee_not_eligible = Employee(
        id=employee_id,
        name="Employee",
        email="employee@example.test",
        cost_center_id=uuid4(),
        is_eligible_for_booking=False,
    )
    use_case = JoinWaitlistUseCase(
        FakeWaitlistRepository([]),
        FakeWorkspaceRepository(None),
        FakeEmployeeRepository(employee_not_eligible),
        FakeBookingRepository(),
        FakeUnitOfWork(),
    )

    with pytest.raises(ValueError, match="Workspace not found"):
        await use_case.execute(workspace_id, employee_id, slot)
