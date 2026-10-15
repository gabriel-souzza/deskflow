from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.availability_window import AvailabilityWindow


class RepositoryConflictError(Exception):
    """Raised when an optimistic lock conflict occurs."""


class AvailabilityWindowRepository(ABC):
    @abstractmethod
    async def get_by_key(
        self,
        workspace_id: UUID,
        day: str,
        slot_index: int,
    ) -> AvailabilityWindow | None:
        """Retrieve an availability window by composite key."""
        ...

    @abstractmethod
    async def save(
        self,
        window: AvailabilityWindow,
        expected_version: int | None = None,
    ) -> AvailabilityWindow:
        """Persist an availability window (insert or update with optional optimistic lock)."""
        ...

    @abstractmethod
    async def delete_by_day(self, day: str) -> None:
        """Delete generated availability windows for a blocked day."""
        ...

    @abstractmethod
    async def count_by_window(
        self,
        workspace_id: UUID,
        day: str,
        slot_index: int,
    ) -> int:
        """Return the number of confirmed bookings occupying this window.

        Same semantics as BookingRepository.count_by_window; kept here for
        use cases that start from the AvailabilityWindow aggregate.
        """
        ...
