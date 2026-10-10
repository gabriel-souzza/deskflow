from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.notify_waitlist import NotifyWaitlistUseCase
from domain.entities.waitlist import Waitlist
from domain.value_objects.time_slot import TimeSlot


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeWaitlistRepository:
    def __init__(self, entries):
        self.entries = list(entries)
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
