from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from datetime import date


@dataclass(frozen=True, slots=True)
class QuotaPeriod:
    """
    Aggregate root representing a monthly quota period for a cost center.
    Invariant I3: consumed_hours must never exceed total_hours (monotonic consumption).
    """
    cost_center_id: UUID = None
    period_start: date = None
    period_end: date = None
    total_hours: Decimal = Decimal("0")
    consumed_hours: Decimal = Decimal("0")

    def __post_init__(self):
        if self.cost_center_id is None:
            raise ValueError("cost_center_id is required")
        if self.period_start is None or self.period_end is None:
            raise ValueError("period_start and period_end are required")
        if self.period_start > self.period_end:
            raise ValueError("period_start must be <= period_end")
        if self.total_hours < 0:
            raise ValueError("total_hours cannot be negative")
        if self.consumed_hours < 0:
            raise ValueError("consumed_hours cannot be negative")
        if self.consumed_hours > self.total_hours:
            raise QuotaExceededError(
                f"Consumed hours ({self.consumed_hours}) exceed total ({self.total_hours})"
            )

    def remaining_hours(self) -> Decimal:
        return self.total_hours - self.consumed_hours

    def can_consume(self, hours: Decimal) -> bool:
        return (self.consumed_hours + hours) <= self.total_hours

    def consume(self, hours: Decimal) -> "QuotaPeriod":
        """
        Consume quota hours. Invariant I3: monotonic consumption.
        Returns new instance with updated consumed_hours.
        """
        if hours < 0:
            # Negative hours = refund (only allowed on cancellation)
            if self.consumed_hours + hours < 0:
                raise ValueError("Cannot refund more than consumed")
            new_consumed = self.consumed_hours + hours
        else:
            if not self.can_consume(hours):
                raise QuotaExceededError(
                    f"Insufficient quota: {self.remaining_hours()} remaining, {hours} requested"
                )
            new_consumed = self.consumed_hours + hours

        from dataclasses import replace
        return replace(self, consumed_hours=new_consumed)


class QuotaExceededError(Exception):
    """Raised when quota consumption would exceed total."""
    pass