from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects.time_slot import TimeSlot


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class Booking:
    """
    Aggregate root representing a workspace reservation.
    Invariant I4: Unidirectional state transitions.
    """

    id: UUID = field(default_factory=uuid4)
    workspace_id: UUID = None
    employee_id: UUID = None
    cost_center_id: UUID = None
    slot: TimeSlot = None
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    qr_token: Optional[str] = None

    def __post_init__(self):
        if self.workspace_id is None:
            raise ValueError("workspace_id is required")
        if self.employee_id is None:
            raise ValueError("employee_id is required")
        if self.cost_center_id is None:
            raise ValueError("cost_center_id is required")
        if self.slot is None:
            raise ValueError("slot is required")
        if self.status not in BookingStatus:
            raise ValueError(f"Invalid status: {self.status}")

    def confirm(self) -> "Booking":
        """Transition PENDING -> CONFIRMED (invariant I4)."""
        if self.status != BookingStatus.PENDING:
            raise InvalidStateTransitionError(f"Cannot confirm booking in status {self.status}")
        return _replace(
            self,
            status=BookingStatus.CONFIRMED,
            modified_at=datetime.now(datetime.timezone.utc),
        )

    def cancel(self) -> "Booking":
        """Transition CONFIRMED/PENDING -> CANCELLED (invariant I4)."""
        if self.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise InvalidStateTransitionError(f"Cannot cancel booking in status {self.status}")
        return _replace(
            self,
            status=BookingStatus.CANCELLED,
            modified_at=datetime.now(datetime.timezone.utc),
        )

    def expire(self) -> "Booking":
        """Transition PENDING -> EXPIRED (invariant I4)."""
        if self.status != BookingStatus.PENDING:
            raise InvalidStateTransitionError(f"Cannot expire booking in status {self.status}")
        return _replace(
            self,
            status=BookingStatus.EXPIRED,
            modified_at=datetime.now(datetime.timezone.utc),
        )

    @property
    def duration_hours(self) -> Decimal:
        return self.slot.duration_hours


def _replace(obj, **changes):
    """Helper to preserve immutability while updating fields."""
    from dataclasses import replace

    return replace(obj, **changes)


class InvalidStateTransitionError(Exception):
    """Raised when a booking state transition is invalid."""

    pass
