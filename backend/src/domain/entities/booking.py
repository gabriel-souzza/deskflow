from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
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
    workspace_id: UUID = field(default=None, kw_only=True)
    employee_id: UUID = field(default=None, kw_only=True)
    cost_center_id: UUID = field(default=None, kw_only=True)
    slot: TimeSlot = field(default=None, kw_only=True)
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
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
        if not isinstance(self.status, BookingStatus):
            raise ValueError(f"Invalid status: {self.status}")

    def confirm(self) -> "Booking":
        """Transition PENDING -> CONFIRMED (invariant I4)."""
        if self.status != BookingStatus.PENDING:
            raise InvalidStateTransitionError(f"Cannot confirm booking in status {self.status}")
        return _replace(
            self,
            status=BookingStatus.CONFIRMED,
            modified_at=datetime.now(UTC),
        )

    def cancel(self) -> "Booking":
        """Transition CONFIRMED/PENDING -> CANCELLED (invariant I4)."""
        if self.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise InvalidStateTransitionError(f"Cannot cancel booking in status {self.status}")
        return _replace(
            self,
            status=BookingStatus.CANCELLED,
            modified_at=datetime.now(UTC),
        )

    def expire(self) -> "Booking":
        """Transition PENDING -> EXPIRED (invariant I4)."""
        if self.status != BookingStatus.PENDING:
            raise InvalidStateTransitionError(f"Cannot expire booking in status {self.status}")
        return _replace(
            self,
            status=BookingStatus.EXPIRED,
            modified_at=datetime.now(UTC),
        )

    @property
    def duration_hours(self) -> Decimal:
        return self.slot.duration_hours


def _replace(obj, **changes):
    """Helper to preserve immutability while updating fields."""
    return replace(obj, **changes)


class InvalidStateTransitionError(Exception):
    """Raised when a booking state transition is invalid."""

    pass
