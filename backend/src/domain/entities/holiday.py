from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Holiday:
    """Entity representing a blocked holiday or optional working day."""
    id: UUID = field(default_factory=uuid4)
    day: date = None  # Primary key is the date
    description: str = ""

    def __post_init__(self):
        if self.day is None:
            raise ValueError("day is required")

    def is_blocked(self) -> bool:
        return True  # All Holiday entities represent blocked days