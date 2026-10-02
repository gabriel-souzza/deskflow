from datetime import datetime
from domain.value_objects.time_slot import TimeSlot


def test_time_slot_valid():
    ts = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 15))
    assert ts.duration_hours == 0.25


def test_time_slot_invalid_boundary():
    try:
        TimeSlot(start=datetime(2026, 9, 4, 9, 10), end=datetime(2026, 9, 4, 9, 25))
        assert False, "Should reject non-15min boundary"
    except ValueError:
        pass


def test_time_slot_overlaps():
    ts1 = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 15))
    ts2 = TimeSlot(start=datetime(2026, 9, 4, 9, 15), end=datetime(2026, 9, 4, 9, 30))
    assert not ts1.overlaps(ts2)