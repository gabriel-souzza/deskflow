from datetime import date
from uuid import uuid4

import pytest

from application.use_cases.get_availability import GetAvailabilityUseCase
from domain.entities.workspace import Workspace, WorkspaceType


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


class MockHolidayRepo:
    def __init__(self, blocked_days=None):
        self.blocked_days = blocked_days or set()

    async def is_blocked(self, day: date) -> bool:
        return day in self.blocked_days


@pytest.mark.asyncio
async def test_get_availability_filters_by_floor_zone_and_type():
    ws1 = Workspace(
        id=uuid4(), code="A1", floor="1", zone="open", type=WorkspaceType.STATION, capacity=1
    )
    ws2 = Workspace(
        id=uuid4(), code="B2", floor="2", zone="quiet", type=WorkspaceType.STATION, capacity=1
    )
    ws3 = Workspace(
        id=uuid4(), code="M1", floor="1", zone="open", type=WorkspaceType.MEETING_ROOM, capacity=8
    )

    ws_repo = MockWorkspaceRepo([ws1, ws2, ws3])
    booking_repo = MockBookingRepo({(ws1.id, "2026-10-15", 0): 1})
    use_case = GetAvailabilityUseCase(ws_repo, booking_repo)

    # Filter by floor 1
    res_floor1 = await use_case.execute(day=date(2026, 10, 15), floor="1")
    assert len(res_floor1["workspaces"]) == 2
    ws1_data = next(w for w in res_floor1["workspaces"] if w["code"] == "A1")
    assert ws1_data["slots"][0]["seats_available"] == 0
    assert ws1_data["slots"][1]["seats_available"] == 1

    # Filter by meeting rooms
    res_type = await use_case.execute(
        day=date(2026, 10, 15), workspace_type=WorkspaceType.MEETING_ROOM
    )
    assert len(res_type["workspaces"]) == 1
    assert res_type["workspaces"][0]["code"] == "M1"
    assert res_type["workspaces"][0]["capacity"] == 8


@pytest.mark.asyncio
async def test_get_availability_returns_holiday_status():
    ws1 = Workspace(
        id=uuid4(), code="A1", floor="1", zone="open", type=WorkspaceType.STATION, capacity=1
    )
    holiday = date(2026, 12, 25)
    use_case = GetAvailabilityUseCase(
        MockWorkspaceRepo([ws1]),
        MockBookingRepo(),
        MockHolidayRepo(blocked_days={holiday}),
    )

    res = await use_case.execute(day=holiday)
    assert res["is_holiday"] is True
    assert res["workspaces"] == []


@pytest.mark.asyncio
async def test_get_availability_filters_by_workspace_id_and_zone():
    ws1 = Workspace(
        id=uuid4(), code="A1", floor="1", zone="open", type=WorkspaceType.STATION, capacity=1
    )
    ws2 = Workspace(
        id=uuid4(), code="A2", floor="1", zone="quiet", type=WorkspaceType.STATION, capacity=1
    )
    ws_repo = MockWorkspaceRepo([ws1, ws2])
    use_case = GetAvailabilityUseCase(ws_repo, MockBookingRepo())

    # Filter by workspace_id
    res_ws = await use_case.execute(day=date(2026, 10, 15), workspace_id=ws1.id)
    assert len(res_ws["workspaces"]) == 1
    assert res_ws["workspaces"][0]["code"] == "A1"

    # Filter by zone
    res_zone = await use_case.execute(day=date(2026, 10, 15), zone="quiet")
    assert len(res_zone["workspaces"]) == 1
    assert res_zone["workspaces"][0]["code"] == "A2"

