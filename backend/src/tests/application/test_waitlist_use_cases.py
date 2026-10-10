from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.join_waitlist import JoinWaitlistUseCase
from application.use_cases.notify_waitlist import NotifyWaitlistUseCase
from domain.entities.employee import Employee
from domain.entities.waitlist import Waitlist
from domain.entities.workspace import Workspace, WorkspaceType
from domain.value_objects.time_slot import TimeSlot


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeWaitlistRepository:
    def __init__(self, entries):
        self.entries = entries
        self.saved = []

    async def list_all_by_workspace(self, workspace_id):
        return sorted(
            (entry for entry in self.entries if entry.workspace_id == workspace_id),
            key=lambda entry: entry.created_at,
        )

    async def save(self, entry):
        self.saved.append(entry)
        self.entries = [entry if old.id == entry.id else old for old in self.entries]
        return entry

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
    async def count_by_window(self, _workspace_id, _day, _slot_index):
        return 1


class FakePublisher:
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)


def make_entry(workspace_id, employee_id, slot, created_at, notified_at=None):
    return Waitlist(
        workspace_id=workspace_id,
        employee_id=employee_id,
        desired_slot_start=slot.start,
        desired_slot_end=slot.end,
        created_at=created_at,
        notified_at=notified_at,
    )


@pytest.mark.asyncio
async def test_notifies_oldest_waitlist_entry_for_exact_slot_once():
    workspace_id = uuid4()
    slot_start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=2)
    slot_start = slot_start.replace(hour=9, minute=0, second=0, microsecond=0)
    slot = TimeSlot(slot_start, slot_start + timedelta(minutes=15))
    first = make_entry(workspace_id, uuid4(), slot, datetime(2026, 1, 1, tzinfo=UTC))
    second = make_entry(workspace_id, uuid4(), slot, datetime(2026, 1, 2, tzinfo=UTC))
    repository = FakeWaitlistRepository([second, first])
    publisher = FakePublisher()
    use_case = NotifyWaitlistUseCase(repository, publisher, FakeUnitOfWork())

    notified = await use_case.execute(workspace_id, slot)
    repeated = await use_case.execute(workspace_id, slot)

    assert notified is not None and notified.id == first.id
    assert notified.notified_at is not None
    assert repeated is not None and repeated.id == second.id
    assert [event["employee_id"] for event in publisher.events] == [
        str(first.employee_id),
        str(second.employee_id),
    ]


@pytest.mark.asyncio
async def test_waitlist_notification_does_not_match_other_slot_or_workspace():
    workspace_id = uuid4()
    slot_start = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=2)
    slot_start = slot_start.replace(hour=9, minute=0, second=0, microsecond=0)
    slot = TimeSlot(slot_start, slot_start + timedelta(minutes=15))
    entry = make_entry(workspace_id, uuid4(), slot, datetime.now(UTC))
    repository = FakeWaitlistRepository([entry])
    publisher = FakePublisher()
    use_case = NotifyWaitlistUseCase(repository, publisher, FakeUnitOfWork())

    result = await use_case.execute(uuid4(), slot)

    assert result is None
    assert publisher.events == []


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
        FakeBookingRepository(),
        FakeUnitOfWork(),
    )

    first = await use_case.execute(workspace_id, employee_id, slot)
    second = await use_case.execute(workspace_id, employee_id, slot)

    assert first == second
    assert len(repository.entries) == 1
