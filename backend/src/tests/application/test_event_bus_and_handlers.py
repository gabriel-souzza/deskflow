from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from adapters.events.audit_log_handler import AuditLogHandler
from adapters.events.in_memory_event_bus import InMemoryEventBus
from adapters.events.quota_alert_handler import QuotaAlertHandler
from domain.events.events import (
    BookingCancelled,
    BookingConfirmed,
    BookingCreated,
    BookingExpired,
    QuotaConsumed,
)
from domain.value_objects.time_slot import TimeSlot


class MockPublisher:
    def __init__(self):
        self.published = []

    async def publish(self, event: dict) -> None:
        self.published.append(event)


class MockAuditLogRepo:
    def __init__(self):
        self.entries = []

    async def create(self, actor_id, action, entity_type, entity_id, timestamp, reason):
        entry = {
            "actor_id": actor_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": timestamp,
            "reason": reason,
        }
        self.entries.append(entry)
        return entry


class MockWaitlistRepo:
    def __init__(self, entries=None):
        self.entries = entries or []

    async def list_all_by_workspace(self, workspace_id):
        return [e for e in self.entries if e.workspace_id == workspace_id]

    async def save(self, entry):
        return entry


class MockUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


@pytest.mark.asyncio
async def test_event_bus_publishes_to_subscribers():
    bus = InMemoryEventBus()
    received = []

    async def handle_quota(event: QuotaConsumed):
        received.append(event)

    bus.subscribe(QuotaConsumed, handle_quota)
    event = QuotaConsumed(
        cost_center_id=uuid4(),
        period_start=date(2026, 10, 1),
        total_hours=Decimal(100),
        consumed_hours=Decimal(20),
        delta_hours=Decimal(2),
    )
    await bus.publish(event)
    assert len(received) == 1
    assert received[0] == event


@pytest.mark.asyncio
async def test_quota_alert_handler_triggers_80_and_95_percent():
    publisher = MockPublisher()
    handler = QuotaAlertHandler(publisher)
    cost_center_id = uuid4()

    # Consumed goes from 70h to 82h of 100h (crosses 80%)
    event_80 = QuotaConsumed(
        cost_center_id=cost_center_id,
        period_start=date(2026, 10, 1),
        total_hours=Decimal(100),
        consumed_hours=Decimal(82),
        delta_hours=Decimal(12),
    )
    alert = await handler.handle_quota_consumed(event_80)
    assert alert is not None
    assert alert.threshold_percent == 80
    assert len(publisher.published) == 1
    assert publisher.published[0]["type"] == "quota.alert"
    assert publisher.published[0]["threshold_percent"] == 80

    # Consumed goes from 82h to 85h (no new threshold crossed)
    event_no_cross = QuotaConsumed(
        cost_center_id=cost_center_id,
        period_start=date(2026, 10, 1),
        total_hours=Decimal(100),
        consumed_hours=Decimal(85),
        delta_hours=Decimal(3),
    )
    alert_none = await handler.handle_quota_consumed(event_no_cross)
    assert alert_none is None
    assert len(publisher.published) == 1

    # Consumed goes from 85h to 96h (crosses 95%)
    event_95 = QuotaConsumed(
        cost_center_id=cost_center_id,
        period_start=date(2026, 10, 1),
        total_hours=Decimal(100),
        consumed_hours=Decimal(96),
        delta_hours=Decimal(11),
    )
    alert_95 = await handler.handle_quota_consumed(event_95)
    assert alert_95 is not None
    assert alert_95.threshold_percent == 95
    assert len(publisher.published) == 2
    assert publisher.published[1]["threshold_percent"] == 95


@pytest.mark.asyncio
async def test_audit_log_handler_records_all_event_types():
    repo = MockAuditLogRepo()
    handler = AuditLogHandler(repo)
    emp_id = uuid4()
    ws_id = uuid4()
    booking_id = uuid4()
    slot = TimeSlot(
        start=datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
        end=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
    )

    await handler.handle(
        BookingCreated(
            booking_id=booking_id,
            workspace_id=ws_id,
            employee_id=emp_id,
            cost_center_id=uuid4(),
            slot=slot,
        )
    )
    await handler.handle(
        BookingConfirmed(
            booking_id=booking_id,
            workspace_id=ws_id,
            employee_id=emp_id,
            slot=slot,
        )
    )
    await handler.handle(
        BookingCancelled(
            booking_id=booking_id,
            workspace_id=ws_id,
            employee_id=emp_id,
            slot=slot,
        )
    )
    await handler.handle(
        BookingExpired(
            booking_id=booking_id,
            workspace_id=ws_id,
            employee_id=emp_id,
            slot=slot,
        )
    )
    await handler.handle(
        QuotaConsumed(
            cost_center_id=uuid4(),
            period_start=date(2026, 10, 1),
            total_hours=Decimal(50),
            consumed_hours=Decimal(10),
            delta_hours=Decimal(2),
        )
    )

    assert len(repo.entries) == 5
    actions = [e["action"] for e in repo.entries]
    assert actions == ["created", "checked_in", "cancelled", "expired", "quota_consumed"]
