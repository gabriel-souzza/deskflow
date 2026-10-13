from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from domain.events.events import (
    BookingCancelled,
    BookingConfirmed,
    BookingCreated,
    BookingExpired,
    DomainEvent,
    QuotaAlert,
    QuotaConsumed,
    WaitlistJoined,
    WaitlistNotified,
)
from domain.value_objects.time_slot import TimeSlot


def _slot():
    return TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 15))


def test_domain_events_instantiation():
    event = DomainEvent()
    assert event.occurred_at is not None

    b_id, w_id, e_id, cc_id = uuid4(), uuid4(), uuid4(), uuid4()
    slot = _slot()

    created = BookingCreated(
        booking_id=b_id,
        workspace_id=w_id,
        employee_id=e_id,
        cost_center_id=cc_id,
        slot=slot,
    )
    assert created.booking_id == b_id

    confirmed = BookingConfirmed(
        booking_id=b_id,
        workspace_id=w_id,
        employee_id=e_id,
        slot=slot,
    )
    assert confirmed.booking_id == b_id

    cancelled = BookingCancelled(
        booking_id=b_id,
        workspace_id=w_id,
        employee_id=e_id,
        slot=slot,
    )
    assert cancelled.booking_id == b_id

    expired = BookingExpired(
        booking_id=b_id,
        workspace_id=w_id,
        employee_id=e_id,
        slot=slot,
    )
    assert expired.booking_id == b_id

    quota_consumed = QuotaConsumed(
        cost_center_id=cc_id,
        period_start=date(2026, 9, 1),
        total_hours=Decimal(100),
        consumed_hours=Decimal(10),
        delta_hours=Decimal("0.25"),
    )
    assert quota_consumed.total_hours == Decimal(100)

    alert = QuotaAlert(
        cost_center_id=cc_id,
        threshold_percent=80,
        consumed_hours=Decimal(80),
        total_hours=Decimal(100),
    )
    assert alert.threshold_percent == 80

    wl_id = uuid4()
    joined = WaitlistJoined(
        waitlist_id=wl_id,
        workspace_id=w_id,
        employee_id=e_id,
        slot=slot,
    )
    assert joined.waitlist_id == wl_id

    notified = WaitlistNotified(
        waitlist_id=wl_id,
        workspace_id=w_id,
        employee_id=e_id,
        slot=slot,
        expires_at=datetime(2026, 9, 4, 10, 0),
    )
    assert notified.expires_at == datetime(2026, 9, 4, 10, 0)
