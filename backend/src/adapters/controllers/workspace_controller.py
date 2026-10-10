import json
from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_admin, require_auth
from adapters.events.sse_publisher import sse_publisher
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.holiday_repo_postgres import HolidayRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.get_availability import GetAvailabilityUseCase
from application.use_cases.manage_workspace import ManageWorkspaceUseCase
from domain.entities.workspace import Workspace, WorkspaceType
from domain.repositories.workspace_repository import WorkspaceInUseError
from infra.database import get_db
from infra.models import WorkspaceORM
from infra.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    floor: str = Field(min_length=1, max_length=100)
    zone: str = Field(min_length=1, max_length=100)
    type: Literal["estacao", "sala"] = "estacao"
    capacity: int = Field(default=1, ge=1)
    resources: list[str] = Field(default_factory=list)


@router.get("/api/v1/workspaces")
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkspaceORM).order_by(WorkspaceORM.code))
    return {
        "items": [
            {
                "id": str(item.id),
                "code": item.code,
                "floor": item.floor,
                "zone": item.zone,
                "type": item.type,
                "capacity": item.capacity,
                "resources": json.loads(item.resources or "[]"),
            }
            for item in result.scalars().all()
        ]
    }


@router.get("/api/v1/workspaces/{id}/availability")
async def get_availability(
    id: UUID,
    day: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.get(WorkspaceORM, id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    use_case = GetAvailabilityUseCase(
        WorkspaceRepositoryPostgres(db),
        BookingRepositoryPostgres(db),
        HolidayRepositoryPostgres(db),
    )
    result = await use_case.execute(day=day, workspace_id=id)
    workspaces_found = result.get("workspaces", [])
    slots = workspaces_found[0]["slots"] if workspaces_found else []
    return {"workspace_id": str(id), "day": day.isoformat(), "slots": slots}


@router.get("/api/v1/availability")
async def get_all_availability(
    current_user: Annotated[dict, Depends(require_auth)],
    day: date = Query(...),
    floor: str | None = Query(default=None),
    zone: str | None = Query(default=None),
    type: Literal["estacao", "sala"] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/availability — UC01: Consultar Disponibilidade com filtros."""
    ws_type = WorkspaceType(type) if type else None
    use_case = GetAvailabilityUseCase(
        WorkspaceRepositoryPostgres(db),
        BookingRepositoryPostgres(db),
        HolidayRepositoryPostgres(db),
    )
    result = await use_case.execute(day=day, floor=floor, zone=zone, workspace_type=ws_type)
    return result


@router.post("/api/v1/admin/workspaces", status_code=201)
async def create_workspace(
    payload: WorkspaceCreate,
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.type == "estacao" and payload.capacity != 1:
        raise HTTPException(status_code=422, detail="Station capacity must be 1")
    existing = await db.scalar(select(WorkspaceORM).where(WorkspaceORM.code == payload.code))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Workspace code already exists")

    workspace = Workspace(
        code=payload.code,
        floor=payload.floor,
        zone=payload.zone,
        type=WorkspaceType(payload.type),
        capacity=payload.capacity,
    )
    try:
        saved = await ManageWorkspaceUseCase(
            WorkspaceRepositoryPostgres(db), SqlAlchemyUnitOfWork(db)
        ).create(workspace)
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Workspace could not be created") from exc
    orm = await db.get(WorkspaceORM, saved.id)
    if orm is not None:
        orm.resources = json.dumps(payload.resources)
        await db.commit()
    await sse_publisher.publish({"type": "workspace.created", "workspace_id": str(saved.id)})
    return {
        "id": str(saved.id),
        "code": saved.code,
        "floor": saved.floor,
        "zone": saved.zone,
        "type": saved.type.value,
        "capacity": saved.capacity,
        "resources": payload.resources,
    }


@router.delete("/api/v1/admin/workspaces/{id}", status_code=204)
async def delete_workspace(
    id: UUID,
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    use_case = ManageWorkspaceUseCase(WorkspaceRepositoryPostgres(db), SqlAlchemyUnitOfWork(db))
    try:
        await use_case.delete(id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkspaceInUseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
