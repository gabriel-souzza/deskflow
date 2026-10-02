from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Tuple, Iterator


@dataclass(frozen=True, slots=True)
class TimeSlot:
    """
    Value Object representing a 15-minute time slot.
    Invariant I1: Slot must be aligned to 15-minute grid.
    """
    start: datetime
    end: datetime

    def __post_init__(self):
        # Invariant I1: start and end must be aligned to 15-minute grid
        if self.start.minute not in {0, 15, 30, 45}:
            raise ValueError(f"Start time must be on 15-minute boundary: {self.start}")
        if self.end.minute not in {0, 15, 30, 45}:
            raise ValueError(f"End time must be on 15-minute boundary: {self.end}")
        if self.start.second != 0 or self.end.second != 0:
            raise ValueError("Seconds must be zero")
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")
        # Ensure duration is a multiple of 15 minutes
        duration_minutes = (self.end - self.start).total_seconds() / 60
        if duration_minutes % 15 != 0:
            raise ValueError("Duration must be a multiple of 15 minutes")

    def overlaps(self, other: "TimeSlot") -> bool:
        """Check if this time slot overlaps with another."""
        return self.start < other.end and other.start < self.end

    def contains(self, instant: datetime) -> bool:
        """Check if an instant falls within [start, end)."""
        return self.start <= instant < self.end

    def slots(self) -> Iterator[datetime]:
        """Yield each 15-minute sub-slot within this slot."""
        current = self.start
        while current < self.end:
            yield current
            current = current.replace(minute=current.minute + 15)

    @property
    def duration_hours(self) -> Decimal:
        """Duration in hours as Decimal."""
        return Decimal((self.end - self.start).total_seconds() / 3600)