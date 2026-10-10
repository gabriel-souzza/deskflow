from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_auth, require_booking_owner
from adapters.events.sse_publisher import sse_publisher
from adapters.repositories.audit_log_repo_postgres import AuditLogRepositoryPostgres
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.employee_repo_postgres import EmployeeRepositoryPostgres
from adapters.repositories.quota_repo_postgres import QuotaRepositoryPostgres
from adapters.repositories.waitlist_repo_postgres import WaitlistRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.cancel_booking import (
    BookingAccessDeniedError,
    BookingCancellationError,
    BookingNotFoundError,
    CancelBookingUseCase,
)
from application.use_cases.create_booking import (
    CreateBookingCommand,
    CreateBookingUseCase,
)
from application.use_cases.notify_waitlist import NotifyWaitlistUseCase
from domain.value_objects.time_slot import TimeSlot
from infra.database import get_db
from infra.security import create_access_token
from infra.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@router.post("", status_code=201)
async def create_booking(
    workspace_id: UUID,
    employee_id: UUID,
    cost_center_id: UUID,
    slot_start: datetime,
    slot_end: datetime,
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    require_booking_owner(current_user, employee_id)
    start = _aware_utc(slot_start)
    end = _aware_utc(slot_end)
    try:
        slot = TimeSlot(start=start, end=end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    use_case = CreateBookingUseCase(
        booking_repo=BookingRepositoryPostgres(db),
        workspace_repo=WorkspaceRepositoryPostgres(db),
        employee_repo=EmployeeRepositoryPostgres(db),
        quota_repo=QuotaRepositoryPostgres(db),
        audit_log_repo=AuditLogRepositoryPostgres(db),
        unit_of_work=SqlAlchemyUnitOfWork(db),
    )
    result = await use_case.execute(
        CreateBookingCommand(workspace_id, employee_id, cost_center_id, slot)
    )
    if result.status_code != 201 or result.booking is None:
        raise HTTPException(status_code=result.status_code, detail=result.message)

    now = datetime.now(UTC)
    booking_id = result.booking.id
    checkin_tolerance = (
        15 if result.workspace_type and result.workspace_type.value == "sala" else 10
    )
    token_expiry = max(timedelta(minutes=10), start - now + timedelta(minutes=checkin_tolerance))
    qr_token = create_access_token(
        {"sub": str(booking_id), "purpose": "booking-checkin"},
        expires_delta=token_expiry,
    )
    await sse_publisher.publish({"type": "booking.created", "booking_id": str(booking_id)})
    return {
        "id": str(booking_id),
        "status": "PENDING",
        "workspace_id": str(workspace_id),
        "qr_token": qr_token,
    }


@router.delete("/{id}")
async def cancel_booking(
    id: UUID,
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    actor_id = current_user.get("employee_id")
    try:
        requester_id = UUID(actor_id) if actor_id else None
    except (TypeError, ValueError):
        requester_id = None
    try:
        cancelled = await CancelBookingUseCase(
            booking_repo=BookingRepositoryPostgres(db),
            quota_repo=QuotaRepositoryPostgres(db),
            audit_log_repo=AuditLogRepositoryPostgres(db),
            unit_of_work=SqlAlchemyUnitOfWork(db),
        ).execute(
            id,
            requester_id,
            is_admin=current_user.get("role") == "admin",
        )
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BookingAccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BookingCancellationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await NotifyWaitlistUseCase(
        WaitlistRepositoryPostgres(db), sse_publisher, SqlAlchemyUnitOfWork(db)
    ).execute(cancelled.workspace_id, cancelled.slot)
    await sse_publisher.publish({"type": "booking.cancelled", "booking_id": str(id)})
    return {"id": str(id), "status": cancelled.status.value}
