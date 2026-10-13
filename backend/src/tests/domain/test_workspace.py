import pytest

from domain.entities.workspace import Workspace, WorkspaceType


def test_workspace_station_valid():
    ws = Workspace(
        code="W01",
        floor="1",
        zone="A",
        type=WorkspaceType.STATION,
        capacity=1,
    )
    assert ws.code == "W01"
    assert ws.floor == "1"
    assert ws.zone == "A"
    assert ws.type == WorkspaceType.STATION
    assert ws.capacity == 1


def test_workspace_meeting_room_valid():
    ws = Workspace(
        code="MR01",
        floor="2",
        zone="B",
        type=WorkspaceType.MEETING_ROOM,
        capacity=8,
    )
    assert ws.type == WorkspaceType.MEETING_ROOM
    assert ws.capacity == 8


def test_workspace_station_capacity_must_be_one():
    with pytest.raises(ValueError, match="Station capacity must be 1"):
        Workspace(
            code="W02",
            floor="1",
            zone="A",
            type=WorkspaceType.STATION,
            capacity=2,
        )


def test_workspace_capacity_must_be_positive():
    with pytest.raises(ValueError, match="capacity must be >= 1"):
        Workspace(
            code="MR02",
            floor="1",
            zone="A",
            type=WorkspaceType.MEETING_ROOM,
            capacity=0,
        )


def test_workspace_validation_errors():
    with pytest.raises(ValueError, match="code is required"):
        Workspace(code=None, floor="1", zone="A")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="floor is required"):
        Workspace(code="W01", floor=None, zone="A")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="zone is required"):
        Workspace(code="W01", floor="1", zone=None)  # type: ignore[arg-type]
