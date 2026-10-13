from uuid import uuid4

import pytest

from domain.entities.availability_window import AvailabilityWindow
from domain.value_objects.capacity import Capacity


def test_availability_window_valid_creation():
    ws_id = uuid4()
    cap = Capacity(seats=10)
    window = AvailabilityWindow(
        workspace_id=ws_id,
        day="2026-09-04",
        slot_index=4,
        capacity=cap,
    )
    assert window.workspace_id == ws_id
    assert window.day == "2026-09-04"
    assert window.slot_index == 4
    assert window.capacity == cap
    assert window.version_id == 1


def test_availability_window_is_full_invariant_i2():
    window = AvailabilityWindow(
        workspace_id=uuid4(),
        day="2026-09-04",
        slot_index=0,
        capacity=Capacity(seats=3),
    )
    assert not window.is_full(confirmed_count=0)
    assert not window.is_full(confirmed_count=2)
    assert window.is_full(confirmed_count=3)
    assert window.is_full(confirmed_count=4)


def test_availability_window_seats_available():
    window = AvailabilityWindow(
        workspace_id=uuid4(),
        day="2026-09-04",
        slot_index=0,
        capacity=Capacity(seats=5),
    )
    assert window.seats_available(confirmed_count=2) == 3
    assert window.seats_available(confirmed_count=5) == 0
    assert window.seats_available(confirmed_count=7) == 0


def test_availability_window_increment_version_invariant_i6():
    window = AvailabilityWindow(
        workspace_id=uuid4(),
        day="2026-09-04",
        slot_index=0,
        capacity=Capacity(seats=2),
        version_id=1,
    )
    next_window = window.increment_version()
    assert next_window.version_id == 2
    assert window.version_id == 1  # Immutability preserved


def test_availability_window_validation_errors():
    ws_id = uuid4()
    cap = Capacity(seats=1)

    with pytest.raises(ValueError, match="workspace_id is required"):
        AvailabilityWindow(workspace_id=None, day="2026-09-04", slot_index=0, capacity=cap)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="day is required"):
        AvailabilityWindow(workspace_id=ws_id, day=None, slot_index=0, capacity=cap)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="slot_index must be non-negative"):
        AvailabilityWindow(workspace_id=ws_id, day="2026-09-04", slot_index=-1, capacity=cap)

    with pytest.raises(ValueError, match="capacity is required"):
        AvailabilityWindow(workspace_id=ws_id, day="2026-09-04", slot_index=0, capacity=None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="version_id must be >= 1"):
        AvailabilityWindow(workspace_id=ws_id, day="2026-09-04", slot_index=0, capacity=cap, version_id=0)
