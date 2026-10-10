from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from application.use_cases.manage_workspace import ManageWorkspaceUseCase
from domain.entities.workspace import Workspace, WorkspaceType


class MockWorkspaceRepo:
    def __init__(self):
        self.workspaces = {}

    async def save(self, workspace: Workspace) -> Workspace:
        self.workspaces[workspace.id] = workspace
        return workspace

    async def delete(self, workspace_id) -> bool:
        if workspace_id in self.workspaces:
            del self.workspaces[workspace_id]
            return True
        return False


class MockUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


@pytest.mark.asyncio
async def test_manage_workspace_create_update_and_delete():
    repo = MockWorkspaceRepo()
    uow = MockUnitOfWork()
    use_case = ManageWorkspaceUseCase(repo, uow)

    ws = Workspace(
        id=uuid4(),
        code="W-10",
        floor="1",
        zone="south",
        type=WorkspaceType.STATION,
        capacity=1,
    )
    saved = await use_case.create(ws)
    assert saved.code == "W-10"
    assert saved.id in repo.workspaces

    updated = await use_case.update(ws)
    assert updated.code == "W-10"

    await use_case.delete(ws.id)
    assert ws.id not in repo.workspaces

    with pytest.raises(LookupError, match="Workspace not found"):
        await use_case.delete(uuid4())
