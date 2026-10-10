from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
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
