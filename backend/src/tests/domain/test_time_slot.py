from datetime import datetime
from decimal import Decimal

import pytest

from domain.value_objects.time_slot import TimeSlot


def test_time_slot_valid():
    ts = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 15))
    assert ts.duration_hours == Decimal("0.25")


def test_time_slot_invalid_boundary_minute():
    with pytest.raises(ValueError, match="Start time must be on 15-minute boundary"):
        TimeSlot(start=datetime(2026, 9, 4, 9, 10), end=datetime(2026, 9, 4, 9, 25))

    with pytest.raises(ValueError, match="End time must be on 15-minute boundary"):
        TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 10))


def test_time_slot_invalid_seconds_and_microseconds():
    with pytest.raises(ValueError, match="Seconds must be zero"):
        TimeSlot(start=datetime(2026, 9, 4, 9, 0, 1), end=datetime(2026, 9, 4, 9, 15))

    with pytest.raises(ValueError, match="Microseconds must be zero"):
        TimeSlot(start=datetime(2026, 9, 4, 9, 0, 0, 500), end=datetime(2026, 9, 4, 9, 15))


def test_time_slot_start_not_before_end():
    with pytest.raises(ValueError, match="Start time must be before end time"):
        TimeSlot(start=datetime(2026, 9, 4, 10, 0), end=datetime(2026, 9, 4, 9, 0))

    with pytest.raises(ValueError, match="Start time must be before end time"):
        TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 0))


def test_time_slot_duration_multiple_of_15():
    # start 9:00, end 9:15 is multiple of 15 (15 min)
    ts = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 10, 0))
    assert ts.duration_hours == Decimal("1.0")


def test_time_slot_overlaps():
    ts1 = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 30))
    ts2 = TimeSlot(start=datetime(2026, 9, 4, 9, 15), end=datetime(2026, 9, 4, 9, 45))
    ts3 = TimeSlot(start=datetime(2026, 9, 4, 9, 30), end=datetime(2026, 9, 4, 10, 0))

    assert ts1.overlaps(ts2)
    assert ts2.overlaps(ts1)
    assert not ts1.overlaps(ts3)  # adjacent is not overlapping


def test_time_slot_contains():
    ts = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 30))
    assert ts.contains(datetime(2026, 9, 4, 9, 0))
    assert ts.contains(datetime(2026, 9, 4, 9, 15))
    assert not ts.contains(datetime(2026, 9, 4, 9, 30))  # end is exclusive
    assert not ts.contains(datetime(2026, 9, 4, 8, 59))
    assert not ts.contains(datetime(2026, 9, 4, 10, 0))


def test_time_slot_slots_iterator():
    ts = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 10, 0))
    sub_slots = list(ts.slots())
    assert len(sub_slots) == 4
    assert sub_slots[0] == datetime(2026, 9, 4, 9, 0)
    assert sub_slots[1] == datetime(2026, 9, 4, 9, 15)
    assert sub_slots[2] == datetime(2026, 9, 4, 9, 30)
    assert sub_slots[3] == datetime(2026, 9, 4, 9, 45)