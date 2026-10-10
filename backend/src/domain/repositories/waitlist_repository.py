from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.waitlist import Waitlist
from domain.value_objects.time_slot import TimeSlot


class WaitlistRepository(ABC):
    @abstractmethod
    async def get_by_workspace_employee(
        self,
        workspace_id: UUID,
        employee_id: UUID,
    ) -> Waitlist | None:
        """Find the Waitlist entry for a specific workspace-employee pair."""
        ...

    @abstractmethod
    async def create(
        self,
        workspace_id: UUID,
        employee_id: UUID,
        desired_slot: TimeSlot,
    ) -> Waitlist:
        """Create a new waitlist entry."""
        ...

    @abstractmethod
    async def save(self, entry: Waitlist) -> Waitlist:
        """Persist a changed waitlist entry."""
        ...

    @abstractmethod
    async def delete(self, waitlist_id: UUID) -> None:
        """Delete a waitlist entry."""
        ...

    @abstractmethod
    async def list_all_by_workspace(
        self,
        workspace_id: UUID,
    ) -> list[Waitlist]:
        """List all waitlist entries for a workspace in creation order."""
        ...
