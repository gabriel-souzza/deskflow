from datetime import datetime
from uuid import uuid4
from domain.entities.booking import Booking, BookingStatus, InvalidStateTransitionError
from domain.value_objects.time_slot import TimeSlot

def test_booking_confirm():
    ts = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 15))
    b = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=ts)
    confirmed = b.confirm()
    assert confirmed.status == BookingStatus.CONFIRMED

def test_booking_invalid_transition():
    ts = TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 15))
    b = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=ts, status=BookingStatus.CONFIRMED)
    try:
        b.confirm()
        assert False
    except InvalidStateTransitionError:
        pass