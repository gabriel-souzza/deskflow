from datetime import UTC, datetime
from uuid import uuid4

import pytest

from domain.entities.waitlist import Waitlist


def test_waitlist_valid_creation():
    ws_id = uuid4()
    emp_id = uuid4()
    start = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
    end = datetime(2026, 9, 4, 10, 0, tzinfo=UTC)

    w = Waitlist(
        workspace_id=ws_id,
        employee_id=emp_id,
        desired_slot_start=start,
        desired_slot_end=end,
    )
    assert w.workspace_id == ws_id
    assert w.employee_id == emp_id
    assert w.desired_slot_start == start
    assert w.desired_slot_end == end
    assert w.notified_at is None
    assert not w.is_notified()


def test_waitlist_mark_notified():
    w = Waitlist(
        workspace_id=uuid4(),
        employee_id=uuid4(),
        desired_slot_start=datetime(2026, 9, 4, 9, 0, tzinfo=UTC),
        desired_slot_end=datetime(2026, 9, 4, 10, 0, tzinfo=UTC),
    )
    notified_time = datetime(2026, 9, 4, 8, 30, tzinfo=UTC)
    w_notified = w.mark_notified(at=notified_time)
    assert w_notified.is_notified()
    assert w_notified.notified_at == notified_time

    # Idempotent: marking again returns the same object without changing notified_at
    later_time = datetime(2026, 9, 4, 8, 45, tzinfo=UTC)
    w_again = w_notified.mark_notified(at=later_time)
    assert w_again.notified_at == notified_time


def test_waitlist_validation_errors():
    valid_dt = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="workspace_id required"):
        Waitlist(
            workspace_id=None,  # type: ignore[arg-type]
            employee_id=uuid4(),
            desired_slot_start=valid_dt,
            desired_slot_end=valid_dt,
        )

    with pytest.raises(ValueError, match="employee_id required"):
        Waitlist(
            workspace_id=uuid4(),
            employee_id=None,  # type: ignore[arg-type]
            desired_slot_start=valid_dt,
            desired_slot_end=valid_dt,
        )
