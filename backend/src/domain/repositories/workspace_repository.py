from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.entities.workspace import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        """Retrieve a workspace by its ID."""
        ...

    @abstractmethod
    async def list_all_active(self) -> list[Workspace]:
        """Return all workspaces marked as active."""
        ...

    @abstractmethod
    async def save(self, workspace: Workspace) -> Workspace:
        """Persist a workspace (insert or update)."""
        ...
