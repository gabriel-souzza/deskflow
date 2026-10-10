from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from domain.value_objects.time_slot import TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingCreated(DomainEvent):
    booking_id: UUID
    workspace_id: UUID
    employee_id: UUID
    cost_center_id: UUID
    slot: TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingConfirmed(DomainEvent):
    booking_id: UUID
    workspace_id: UUID
    employee_id: UUID
    slot: TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingCancelled(DomainEvent):
    booking_id: UUID
    workspace_id: UUID
    employee_id: UUID
    slot: TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingExpired(DomainEvent):
    booking_id: UUID
    workspace_id: UUID
    employee_id: UUID
    slot: TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class QuotaConsumed(DomainEvent):
    cost_center_id: UUID
    period_start: date
    total_hours: Decimal
    consumed_hours: Decimal
    delta_hours: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class QuotaAlert(DomainEvent):
    cost_center_id: UUID
    threshold_percent: int  # 80 or 95
    consumed_hours: Decimal
    total_hours: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class WaitlistJoined(DomainEvent):
    waitlist_id: UUID
    workspace_id: UUID
    employee_id: UUID
    slot: TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class WaitlistNotified(DomainEvent):
    waitlist_id: UUID
    workspace_id: UUID
    employee_id: UUID
    slot: TimeSlot
    expires_at: datetime
