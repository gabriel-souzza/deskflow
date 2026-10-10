from contextlib import asynccontextmanager
from datetime import date
from uuid import uuid4

import pytest

from application.use_cases.block_holidays import BlockHolidaysUseCase
from application.use_cases.generate_daily_availability import GenerateDailyAvailabilityUseCase
from domain.entities.availability_window import AvailabilityWindow
from domain.entities.holiday import Holiday
from domain.entities.workspace import Workspace, WorkspaceType
from domain.value_objects.capacity import Capacity


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeWorkspaceRepository:
    def __init__(self, workspaces):
        self.workspaces = workspaces

    async def list_all_active(self):
        return self.workspaces


class FakeAvailabilityWindowRepository:
    def __init__(self):
        self.windows = {}
        self.deleted_days = []

    async def get_by_key(self, workspace_id, day, slot_index):
        return self.windows.get((workspace_id, day, slot_index))

    async def save(self, window):
        self.windows[(window.workspace_id, window.day, window.slot_index)] = window
        return window

    async def delete_by_day(self, day):
        self.deleted_days.append(day)
        self.windows = {key: value for key, value in self.windows.items() if key[1] != day}


class FakeHolidayRepository:
    def __init__(self):
        self.days = set()
        self.saved = []

    async def is_blocked(self, day):
        return day in self.days

    async def save(self, holiday):
        self.days.add(holiday.day)
        self.saved.append(holiday)
        return holiday


def make_workspace(capacity=1):
    return Workspace(
        id=uuid4(),
        code=f"W-{uuid4()}",
        floor="1",
        zone="test",
        type=WorkspaceType.STATION if capacity == 1 else WorkspaceType.MEETING_ROOM,
        capacity=capacity,
    )


@pytest.mark.asyncio
async def test_daily_availability_creates_forty_windows_once_per_workspace():
    workspaces = [make_workspace(), make_workspace(6)]
    windows = FakeAvailabilityWindowRepository()
    holidays = FakeHolidayRepository()
    use_case = GenerateDailyAvailabilityUseCase(
        windows, FakeWorkspaceRepository(workspaces), holidays, FakeUnitOfWork()
    )

    created = await use_case.execute("2026-10-12")
    repeated = await use_case.execute("2026-10-12")

    assert created == 80
    assert repeated == 0
    assert len(windows.windows) == 80
    assert windows.windows[(workspaces[1].id, "2026-10-12", 39)].capacity == Capacity(seats=6)


@pytest.mark.asyncio
async def test_daily_availability_skips_holidays():
    windows = FakeAvailabilityWindowRepository()
    holidays = FakeHolidayRepository()
    holiday_day = date(2026, 10, 12)
    holidays.days.add(holiday_day)
    use_case = GenerateDailyAvailabilityUseCase(
        windows, FakeWorkspaceRepository([make_workspace()]), holidays, FakeUnitOfWork()
    )

    assert await use_case.execute(holiday_day.isoformat()) == 0
    assert windows.windows == {}


@pytest.mark.asyncio
async def test_block_holiday_persists_holiday_and_deletes_windows():
    windows = FakeAvailabilityWindowRepository()
    holidays = FakeHolidayRepository()
    day = date(2026, 10, 12)
    window = AvailabilityWindow(
        workspace_id=uuid4(),
        day=day.isoformat(),
        slot_index=4,
        capacity=Capacity(seats=1),
    )
    await windows.save(window)
    use_case = BlockHolidaysUseCase(windows, holidays, FakeUnitOfWork())

    result = await use_case.execute(Holiday(day=day, description="Holiday"))

    assert result.is_blocked()
    assert holidays.saved == [result]
    assert windows.deleted_days == [day.isoformat()]
    assert windows.windows == {}
