from domain.repositories.workspace_repository import WorkspaceRepository
from domain.entities.workspace import Workspace, WorkspaceType


class ManageWorkspaceUseCase:
    """UC12: Gerenciar Espaços."""

    def __init__(self, workspace_repo: WorkspaceRepository):
        self.workspace_repo = workspace_repo

    async def create(self, workspace: Workspace) -> Workspace:
        return await self.workspace_repo.save(workspace)

    async def update(self, workspace: Workspace) -> Workspace:
        return await self.workspace_repo.save(workspace)

    async def delete(self, workspace_id: str) -> None:
        pass