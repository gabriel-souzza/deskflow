from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_auth
from adapters.events.sse_publisher import sse_publisher
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.employee_repo_postgres import EmployeeRepositoryPostgres
from adapters.repositories.waitlist_repo_postgres import WaitlistRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.join_waitlist import JoinWaitlistUseCase
from domain.value_objects.time_slot import TimeSlot
from infra.database import get_db
from infra.models import WaitlistORM
from infra.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/waitlist", tags=["waitlist"])


class WaitlistCreate(BaseModel):
    workspace_id: UUID
    slot_start: datetime
    slot_end: datetime


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@router.post("", status_code=201)
async def join_waitlist(
    payload: WaitlistCreate,
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    employee_id = current_user.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=403, detail="Employee account required")
    try:
        employee_uuid = UUID(employee_id)
        slot = TimeSlot(start=_aware_utc(payload.slot_start), end=_aware_utc(payload.slot_end))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid employee or time slot") from exc

    use_case = JoinWaitlistUseCase(
        waitlist_repo=WaitlistRepositoryPostgres(db),
        workspace_repo=WorkspaceRepositoryPostgres(db),
        employee_repo=EmployeeRepositoryPostgres(db),
        booking_repo=BookingRepositoryPostgres(db),
        unit_of_work=SqlAlchemyUnitOfWork(db),
    )
    try:
        entry = await use_case.execute(payload.workspace_id, employee_uuid, slot)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message.endswith("not found") else 409
        if "not eligible" in message:
            status_code = 403
        raise HTTPException(status_code=status_code, detail=message) from exc
    await sse_publisher.publish(
        {
            "type": "waitlist.joined",
            "waitlist_id": str(entry.id),
            "workspace_id": str(entry.workspace_id),
        }
    )
    return {
        "id": str(entry.id),
        "workspace_id": str(entry.workspace_id),
        "slot_start": entry.desired_slot_start.isoformat(),
        "slot_end": entry.desired_slot_end.isoformat(),
        "created_at": entry.created_at.isoformat(),
    }


@router.get("")
async def list_waitlist(
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """GET /api/v1/waitlist — Listar posições na fila de espera (UC05)."""
    emp_id = current_user.get("employee_id")
    if not emp_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Employee account required")

    stmt = select(WaitlistORM).order_by(WaitlistORM.created_at)
    if current_user.get("role") != "admin" and emp_id:
        stmt = stmt.where(WaitlistORM.employee_id == UUID(emp_id))

    result = await db.execute(stmt)
    entries = result.scalars().all()
    return {
        "items": [
            {
                "id": str(e.id),
                "workspace_id": str(e.workspace_id),
                "employee_id": str(e.employee_id),
                "desired_start": e.desired_start.isoformat() if e.desired_start else None,
                "desired_end": e.desired_end.isoformat() if e.desired_end else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "notified_at": e.notified_at.isoformat() if e.notified_at else None,
            }
            for e in entries
        ]
    }


@router.delete("/{id}", status_code=204)
async def leave_waitlist(
    id: UUID,
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """DELETE /api/v1/waitlist/{id} — Cancelar entrada na fila de espera (UC05)."""
    entry = await db.get(WaitlistORM, id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")

    emp_id = current_user.get("employee_id")
    if current_user.get("role") != "admin" and str(entry.employee_id) != emp_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(entry)
    await db.commit()
