from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.entities.availability_window import AvailabilityWindow


class AvailabilityWindowRepository(ABC):
    @abstractmethod
    async def get_by_key(
        self,
        workspace_id: UUID,
        day: str,
        slot_index: int,
    ) -> Optional[AvailabilityWindow]:
        """Retrieve an availability window by composite key."""
        ...

    @abstractmethod
    async def save(self, window: AvailabilityWindow) -> AvailabilityWindow:
        """Persist an availability window (insert or update)."""
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
