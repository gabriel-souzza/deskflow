from uuid import UUID

from domain.entities.workspace import Workspace
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.workspace_repository import WorkspaceRepository


class ManageWorkspaceUseCase:
    """UC12: Gerenciar Espaços."""

    def __init__(self, workspace_repo: WorkspaceRepository, unit_of_work: UnitOfWork):
        self.workspace_repo = workspace_repo
        self.unit_of_work = unit_of_work

    async def create(self, workspace: Workspace) -> Workspace:
        return await self.workspace_repo.save(workspace)

    async def update(self, workspace: Workspace) -> Workspace:
        return await self.workspace_repo.save(workspace)

    async def delete(self, workspace_id: UUID) -> None:
        async with self.unit_of_work.transaction():
            if not await self.workspace_repo.delete(workspace_id):
                raise LookupError("Workspace not found")
