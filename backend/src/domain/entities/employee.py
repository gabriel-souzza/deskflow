from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class Employee:
    """Aggregate root representing an employee who can make bookings."""

    id: UUID = field(default_factory=uuid4)
    name: str
    email: str
    cost_center_id: UUID
    is_eligible_for_booking: bool = False

    def __post_init__(self) -> None:
        if self.name is None:
            raise ValueError("name is required")
        if self.email is None:
            raise ValueError("email is required")
        if self.cost_center_id is None:
            raise ValueError("cost_center_id is required")

    def check_eligibility(self, day: date) -> bool:
        """Validate eligibility for a specific day (política presencial)."""
        return self.is_eligible_for_booking