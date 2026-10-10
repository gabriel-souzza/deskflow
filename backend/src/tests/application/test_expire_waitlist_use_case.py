from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.expire_waitlist import ExpireWaitlistUseCase
from domain.entities.waitlist import Waitlist
from domain.entities.workspace import Workspace, WorkspaceType


class MockPublisher:
    def __init__(self):
        self.published = []

    async def publish(self, event: dict) -> None:
        self.published.append(event)


class MockWaitlistRepo:
    def __init__(self, entries):
        self.entries = list(entries)

    async def list_all_by_workspace(self, workspace_id):
        return [e for e in self.entries if e.workspace_id == workspace_id]

    async def save(self, entry):
        for i, e in enumerate(self.entries):
            if e.id == entry.id:
                self.entries[i] = entry
                return entry
        self.entries.append(entry)
        return entry


class MockWorkspaceRepo:
    def __init__(self, workspaces):
        self.workspaces = workspaces

    async def list_all_active(self):
        return self.workspaces


class MockBookingRepo:
    def __init__(self, counts=None):
        self.counts = counts or {}

    async def count_by_window(self, workspace_id, day_key, slot_index):
        return self.counts.get((workspace_id, day_key, slot_index), 0)


class MockUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


@pytest.mark.asyncio
async def test_expire_waitlist_notifies_next_when_expired_timeout():
    now = datetime.now(UTC)
    ws = Workspace(
        id=uuid4(), code="W-01", floor="1", zone="open", type=WorkspaceType.STATION, capacity=1
    )
    # Aligned to 15-minute grid (Invariant I1)
    start = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)
    end = start + timedelta(minutes=15)

    # Entry 1: notified 10 minutes ago (expired)
    entry1 = Waitlist(
        id=uuid4(),
        workspace_id=ws.id,
        employee_id=uuid4(),
        desired_slot_start=start,
        desired_slot_end=end,
        notified_at=now - timedelta(minutes=10),
    )
    # Entry 2: waiting in line (not notified yet)
    entry2 = Waitlist(
        id=uuid4(),
        workspace_id=ws.id,
        employee_id=uuid4(),
        desired_slot_start=start,
        desired_slot_end=end,
        notified_at=None,
    )

    publisher = MockPublisher()
    waitlist_repo = MockWaitlistRepo([entry1, entry2])
    use_case = ExpireWaitlistUseCase(
        waitlist_repo=waitlist_repo,
        booking_repo=MockBookingRepo(),
        workspace_repo=MockWorkspaceRepo([ws]),
        publisher=publisher,
        unit_of_work=MockUnitOfWork(),
    )

    expired_count = await use_case.execute()
    assert expired_count == 1
    # Entry 2 was notified as next
    assert len(publisher.published) == 1
    assert publisher.published[0]["employee_id"] == str(entry2.employee_id)
