from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Capacity:
    """
    Value Object representing the capacity of an AvailabilityWindow.
    Invariant I2: Capacity.seats is the maximum number of confirmed bookings.
    """
    seats: int
    zone: Optional[str] = None

    def __post_init__(self):
        if self.seats < 0:
            raise ValueError("Capacity seats cannot be negative")
        if self.seats == 0:
            raise ValueError("Capacity seats must be at least 1")