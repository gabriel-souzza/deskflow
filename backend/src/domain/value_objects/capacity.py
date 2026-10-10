from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Capacity:
    """
    Value Object representing the capacity of an AvailabilityWindow.
    Invariant I2: Capacity.seats is the maximum number of confirmed bookings.
    """
    seats: int
    zone: str | None = None

    def __post_init__(self) -> None:
        if self.seats < 0:
            raise ValueError("Capacity seats cannot be negative")
        if self.seats == 0:
            raise ValueError("Capacity seats must be at least 1")