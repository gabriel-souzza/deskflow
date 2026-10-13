from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.entities.booking import Booking, BookingStatus, InvalidStateTransitionError
from domain.value_objects.time_slot import TimeSlot


def _sample_slot():
    return TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 30))


def test_booking_confirm():
    ts = _sample_slot()
    b = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=ts)
    assert b.status == BookingStatus.PENDING
    confirmed = b.confirm()
    assert confirmed.status == BookingStatus.CONFIRMED
    assert b.status == BookingStatus.PENDING  # Immutability


def test_booking_cancel_from_pending():
    b = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=_sample_slot())
    cancelled = b.cancel()
    assert cancelled.status == BookingStatus.CANCELLED


def test_booking_cancel_from_confirmed():
    b = Booking(
        workspace_id=uuid4(),
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        slot=_sample_slot(),
        status=BookingStatus.CONFIRMED,
    )
    cancelled = b.cancel()
    assert cancelled.status == BookingStatus.CANCELLED


def test_booking_expire_from_pending():
    b = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=_sample_slot())
    expired = b.expire()
    assert expired.status == BookingStatus.EXPIRED


def test_booking_invalid_transitions():
    ts = _sample_slot()
    confirmed = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=ts, status=BookingStatus.CONFIRMED)
    cancelled = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=ts, status=BookingStatus.CANCELLED)
    expired = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=ts, status=BookingStatus.EXPIRED)

    # Cannot confirm non-PENDING
    with pytest.raises(InvalidStateTransitionError):
        confirmed.confirm()
    with pytest.raises(InvalidStateTransitionError):
        cancelled.confirm()
    with pytest.raises(InvalidStateTransitionError):
        expired.confirm()

    # Cannot cancel already cancelled or expired
    with pytest.raises(InvalidStateTransitionError):
        cancelled.cancel()
    with pytest.raises(InvalidStateTransitionError):
        expired.cancel()

    # Cannot expire non-PENDING
    with pytest.raises(InvalidStateTransitionError):
        confirmed.expire()
    with pytest.raises(InvalidStateTransitionError):
        cancelled.expire()


def test_booking_duration_hours():
    b = Booking(workspace_id=uuid4(), employee_id=uuid4(), cost_center_id=uuid4(), slot=_sample_slot())
    assert b.duration_hours == Decimal("0.5")


def test_booking_validation_errors():
    ws_id = uuid4()
    emp_id = uuid4()
    cc_id = uuid4()
    ts = _sample_slot()

    with pytest.raises(ValueError, match="workspace_id is required"):
        Booking(workspace_id=None, employee_id=emp_id, cost_center_id=cc_id, slot=ts)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="employee_id is required"):
        Booking(workspace_id=ws_id, employee_id=None, cost_center_id=cc_id, slot=ts)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="cost_center_id is required"):
        Booking(workspace_id=ws_id, employee_id=emp_id, cost_center_id=None, slot=ts)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="slot is required"):
        Booking(workspace_id=ws_id, employee_id=emp_id, cost_center_id=cc_id, slot=None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Invalid status"):
        Booking(workspace_id=ws_id, employee_id=emp_id, cost_center_id=cc_id, slot=ts, status="INVALID")  # type: ignore[arg-type]