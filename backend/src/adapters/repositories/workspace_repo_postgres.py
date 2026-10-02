from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories.workspace_repository import WorkspaceRepository
from domain.entities.workspace import Workspace, WorkspaceType
from infra.models import WorkspaceORM


class WorkspaceRepositoryPostgres(WorkspaceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        result = await self.session.execute(
            select(WorkspaceORM).where(WorkspaceORM.id == workspace_id)
        )
        row = result.scalars().first()
        if not row:
            return None
        return Workspace(id=row.id, code=row.code, floor=row.floor, zone=row.zone, type=WorkspaceType(row.type), capacity=row.capacity)

    async def list_all_active(self) -> List[Workspace]:
        result = await self.session.execute(select(WorkspaceORM))
        return [Workspace(id=r.id, code=r.code, floor=r.floor, zone=r.zone, type=WorkspaceType(r.type), capacity=r.capacity) for r in result.scalars().all()]

    async def save(self, workspace: Workspace) -> Workspace:
        orm = WorkspaceORM(
            id=workspace.id,
            code=workspace.code,
            floor=workspace.floor,
            zone=workspace.zone,
            type=workspace.type.value,
            capacity=workspace.capacity,
        )
        self.session.add(orm)
        await self.session.commit()
        return workspace