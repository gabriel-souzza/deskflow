import json
from datetime import date, datetime, time, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.admin_controller import require_admin
from adapters.events.sse_publisher import sse_publisher
from infra.database import get_db
from infra.models import BookingORM, WorkspaceORM

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

    day_start = datetime.combine(day, time(8))
    day_end = datetime.combine(day, time(18))
    result = await db.execute(
        select(BookingORM.slot_start, BookingORM.slot_end).where(
            BookingORM.workspace_id == id,
            BookingORM.status.in_(("PENDING", "CONFIRMED")),
            BookingORM.slot_start < day_end,
            BookingORM.slot_end > day_start,
        )
    )
    bookings = result.all()
    slots = []
    for slot_index in range(40):
        start = day_start + timedelta(minutes=15 * slot_index)
        end = start + timedelta(minutes=15)
        occupied = sum(
            1
            for booking_start, booking_end in bookings
            if booking_start < end and booking_end > start
        )
        slots.append(
            {
                "slot_index": slot_index,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "capacity": workspace.capacity,
                "seats_available": max(0, workspace.capacity - occupied),
            }
        )
    return {"workspace_id": str(id), "day": day.isoformat(), "slots": slots}


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

    workspace = WorkspaceORM(
        code=payload.code,
        floor=payload.floor,
        zone=payload.zone,
        type=payload.type,
        capacity=payload.capacity,
        resources=json.dumps(payload.resources),
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    await sse_publisher.publish({"type": "workspace.created", "workspace_id": str(workspace.id)})
    return {
        "id": str(workspace.id),
        "code": workspace.code,
        "floor": workspace.floor,
        "zone": workspace.zone,
        "type": workspace.type,
        "capacity": workspace.capacity,
        "resources": payload.resources,
    }
