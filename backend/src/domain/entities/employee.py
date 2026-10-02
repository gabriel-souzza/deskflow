from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import date
from typing import Optional


@dataclass(frozen=True, slots=True)
class Employee:
    """Aggregate root representing an employee who can make bookings."""
    id: UUID = field(default_factory=uuid4)
    name: str = None
    email: str = None
    cost_center_id: UUID = None
    is_eligible_for_booking: bool = False

    def __post_init__(self):
        if self.name is None:
            raise ValueError("name is required")
        if self.email is None:
            raise ValueError("email is required")
        if self.cost_center_id is None:
            raise ValueError("cost_center_id is required")

    def check_eligibility(self, day: date) -> bool:
        """Validate eligibility for a specific day (política presencial)."""
        return self.is_eligible_for_booking