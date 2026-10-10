from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.workspace import Workspace, WorkspaceType
from domain.repositories.workspace_repository import WorkspaceInUseError, WorkspaceRepository
from infra.models import BookingORM, WaitlistORM, WorkspaceORM


class WorkspaceRepositoryPostgres(WorkspaceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        result = await self.session.execute(
            select(WorkspaceORM).where(WorkspaceORM.id == workspace_id)
        )
        row = result.scalars().first()
        if not row:
            return None
        return self._to_entity(row)

    async def get_for_booking(self, workspace_id: UUID) -> Workspace | None:
        result = await self.session.execute(
            select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
        )
        row = result.scalars().first()
        return self._to_entity(row)

    @staticmethod
    def _to_entity(row: WorkspaceORM | None) -> Workspace | None:
        if row is None:
            return None
        return Workspace(
            id=row.id,
            code=row.code,
            floor=row.floor,
            zone=row.zone,
            type=WorkspaceType(row.type),
            capacity=row.capacity,
        )

    async def list_all_active(self) -> list[Workspace]:
        result = await self.session.execute(select(WorkspaceORM))
        return [
            Workspace(
                id=r.id,
                code=r.code,
                floor=r.floor,
                zone=r.zone,
                type=WorkspaceType(r.type),
                capacity=r.capacity,
            )
            for r in result.scalars().all()
        ]

    async def save(self, workspace: Workspace) -> Workspace:
        orm = await self.session.get(WorkspaceORM, workspace.id)
        if orm is None:
            orm = WorkspaceORM(id=workspace.id)
            self.session.add(orm)
        orm.code = workspace.code
        orm.floor = workspace.floor
        orm.zone = workspace.zone
        orm.type = workspace.type.value
        orm.capacity = workspace.capacity
        await self.session.flush()
        return workspace

    async def delete(self, workspace_id: UUID) -> bool:
        row = await self.session.get(WorkspaceORM, workspace_id)
        if row is None:
            return False
        booking = await self.session.scalar(
            select(BookingORM.id).where(BookingORM.workspace_id == workspace_id).limit(1)
        )
        waitlist_entry = await self.session.scalar(
            select(WaitlistORM.id).where(WaitlistORM.workspace_id == workspace_id).limit(1)
        )
        if booking is not None or waitlist_entry is not None:
            raise WorkspaceInUseError("Workspace has bookings or waitlist entries")
        await self.session.delete(row)
        await self.session.flush()
        return True
