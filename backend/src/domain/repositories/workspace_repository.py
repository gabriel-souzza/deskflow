from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.workspace import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        """Retrieve a workspace by its ID."""
        ...

    @abstractmethod
    async def get_for_booking(self, workspace_id: UUID) -> Workspace | None:
        """Retrieve and lock a workspace while a booking is created."""
        ...

    @abstractmethod
    async def list_all_active(self) -> list[Workspace]:
        """Return all workspaces marked as active."""
        ...

    @abstractmethod
    async def save(self, workspace: Workspace) -> Workspace:
        """Persist a workspace (insert or update)."""
        ...

    @abstractmethod
    async def delete(self, workspace_id: UUID) -> bool:
        """Delete an unused workspace, returning false when it does not exist."""
        ...


class WorkspaceInUseError(Exception):
    """Raised when a workspace with bookings or waitlist entries cannot be deleted."""
