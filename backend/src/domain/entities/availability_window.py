from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects.capacity import Capacity


@dataclass(frozen=True, slots=True)
class AvailabilityWindow:
    """
    Aggregate root representing an availability window for a workspace.
    Invariant I2: Capacity must never be exceeded (checked via UNIQUE constraint on booking_windows).
    Invariant I6: Optimistic lock via version_id.
    """
    workspace_id: UUID = None
    day: str = None  # ISO format: "2026-09-04"
    slot_index: int = None
    capacity: Capacity = None
    version_id: int = 1

    def __post_init__(self):
        if self.workspace_id is None:
            raise ValueError("workspace_id is required")
        if self.day is None:
            raise ValueError("day is required")
        if self.slot_index is None or self.slot_index < 0:
            raise ValueError("slot_index must be non-negative")
        if self.capacity is None:
            raise ValueError("capacity is required")
        if self.version_id < 1:
            raise ValueError("version_id must be >= 1")

    def is_full(self, confirmed_count: int) -> bool:
        """Check if the window has reached capacity."""
        return confirmed_count >= self.capacity.seats

    def seats_available(self, confirmed_count: int) -> int:
        return max(0, self.capacity.seats - confirmed_count)

    def increment_version(self) -> "AvailabilityWindow":
        """Create a new instance with incremented version (for optimistic locking)."""
        from dataclasses import replace
        return replace(self, version_id=self.version_id + 1)
