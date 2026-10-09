from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from domain.entities.booking import Booking


class BookingRepository(ABC):
    @abstractmethod
    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        """Retrieve a booking by its ID."""
        ...

    @abstractmethod
    async def save(self, booking: Booking) -> Booking:
        """Persist a booking and its BookingWindow associations atomically."""
        ...

    @abstractmethod
    async def delete_by_booking(self, booking_id: UUID) -> None:
        """Delete the BookingWindow associations for a given booking."""
        ...

    @abstractmethod
    async def find_pending_expired(
        self,
        station_cutoff: datetime,
        meeting_room_cutoff: datetime,
    ) -> list[Booking]:
        """Find pending bookings past the check-in grace period for their workspace type."""
        ...

    @abstractmethod
    async def count_by_window(
        self,
        workspace_id: UUID,
        day: str,
        slot_index: int,
    ) -> int:
        """Count confirmed bookings occupying a specific AvailabilityWindow.

        Used by invariant I2 (capacity never exceeded). The concrete
        implementation must return the number of confirmed BookingWindow rows
        for (workspace_id, day, slot_index).
        """
        ...
