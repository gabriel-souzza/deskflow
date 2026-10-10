from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Waitlist:
    """Aggregate root representing a FIFO waitlist entry."""

    id: UUID = field(default_factory=uuid4)
    workspace_id: UUID = None
    employee_id: UUID = None
    desired_slot_start: datetime = None
    desired_slot_end: datetime = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notified_at: Optional[datetime] = None

    def __post_init__(self):
        if self.workspace_id is None:
            raise ValueError("workspace_id required")
        if self.employee_id is None:
            raise ValueError("employee_id required")

    def is_notified(self) -> bool:
        return self.notified_at is not None

    def mark_notified(self, at: datetime | None = None) -> "Waitlist":
        if self.is_notified():
            return self
        return replace(self, notified_at=at or datetime.now(UTC))
