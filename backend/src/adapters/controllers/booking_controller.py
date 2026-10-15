from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_auth, require_booking_owner
from adapters.events.in_memory_event_bus import event_bus
from adapters.events.sse_publisher import sse_publisher
from adapters.repositories.audit_log_repo_postgres import AuditLogRepositoryPostgres
from adapters.repositories.availability_window_repo_postgres import (
    AvailabilityWindowRepositoryPostgres,
)
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


class CreateBookingRequest(BaseModel):
    workspace_id: UUID
    employee_id: UUID
    cost_center_id: UUID
    slot_start: datetime
    slot_end: datetime


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@router.post("", status_code=201)
async def create_booking(
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: CreateBookingRequest | None = None,
    workspace_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    cost_center_id: UUID | None = Query(default=None),
    slot_start: datetime | None = Query(default=None),
    slot_end: datetime | None = Query(default=None),
):
    ws_id = payload.workspace_id if payload else workspace_id
    emp_id = payload.employee_id if payload else employee_id
    cc_id = payload.cost_center_id if payload else cost_center_id
    s_start = payload.slot_start if payload else slot_start
    s_end = payload.slot_end if payload else slot_end

    if not all([ws_id, emp_id, cc_id, s_start, s_end]):
        raise HTTPException(
            status_code=422,
            detail="workspace_id, employee_id, cost_center_id, slot_start, and slot_end are required",
        )

    require_booking_owner(current_user, emp_id)
    start = _aware_utc(s_start)
    end = _aware_utc(s_end)
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
        window_repo=AvailabilityWindowRepositoryPostgres(db),
        event_bus=event_bus,
    )
    result = await use_case.execute(
        CreateBookingCommand(ws_id, emp_id, cc_id, slot)
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
        "workspace_id": str(ws_id),
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
            event_bus=event_bus,
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


@router.get("")
async def list_bookings(
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
    employee_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """GET /api/v1/bookings — Listar reservas do colaborador ou geral para admin."""
    target_id = employee_id
    if target_id is None:
        user_emp = current_user.get("employee_id")
        if user_emp:
            try:
                target_id = UUID(user_emp)
            except ValueError:
                target_id = None

    if target_id is None and current_user.get("role") != "admin":
        raise HTTPException(status_code=400, detail="employee_id is required")

    repo = BookingRepositoryPostgres(db)
    if target_id is not None:
        require_booking_owner(current_user, target_id)
        bookings = await repo.list_by_employee(target_id, status=status)
    else:
        now = datetime.now(UTC)
        bookings = await repo.list_between(now - timedelta(days=365), now + timedelta(days=365))
        if status:
            bookings = [b for b in bookings if b.status.value.upper() == status.upper()]

    return {
        "items": [
            {
                "id": str(b.id),
                "workspace_id": str(b.workspace_id),
                "employee_id": str(b.employee_id),
                "cost_center_id": str(b.cost_center_id),
                "slot_start": b.slot.start.isoformat(),
                "slot_end": b.slot.end.isoformat(),
                "status": b.status.value,
                "created_at": b.created_at.isoformat(),
            }
            for b in bookings
        ]
    }


@router.get("/{id}")
async def get_booking(
    id: UUID,
    current_user: Annotated[dict, Depends(require_auth)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """GET /api/v1/bookings/{id} — Obter detalhes de uma reserva específica."""
    repo = BookingRepositoryPostgres(db)
    booking = await repo.get_by_id(id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    require_booking_owner(current_user, booking.employee_id)
    return {
        "id": str(booking.id),
        "workspace_id": str(booking.workspace_id),
        "employee_id": str(booking.employee_id),
        "cost_center_id": str(booking.cost_center_id),
        "slot_start": booking.slot.start.isoformat(),
        "slot_end": booking.slot.end.isoformat(),
        "status": booking.status.value,
        "created_at": booking.created_at.isoformat(),
    }
