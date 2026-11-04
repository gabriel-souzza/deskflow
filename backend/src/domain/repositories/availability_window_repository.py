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

    async def get_or_create(
        self,
        workspace_id: UUID,
        day: str,
        slot_index: int,
        default_seats: int = 1,
    ) -> AvailabilityWindow:
        """Retrieve an availability window or create it if absent (ensures lockable entity)."""
        window = await self.get_by_key(workspace_id, day, slot_index)
        if window is not None:
            return window
        from domain.value_objects.capacity import Capacity

        new_window = AvailabilityWindow(
            workspace_id=workspace_id,
            day=day,
            slot_index=slot_index,
            capacity=Capacity(seats=default_seats),
            version_id=1,
        )
        return await self.save(new_window)

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
