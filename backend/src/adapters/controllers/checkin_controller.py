from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_auth, require_booking_owner
from adapters.events.in_memory_event_bus import event_bus
from adapters.events.sse_publisher import sse_publisher
from adapters.repositories.audit_log_repo_postgres import AuditLogRepositoryPostgres
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.confirm_booking import (
    BookingNotFoundError,
    CheckInError,
    ConfirmBookingUseCase,
)
from domain.entities.booking import BookingStatus
from infra.database import get_db
from infra.qr_generator import generate_qr_png_bytes
from infra.security import create_access_token, verify_token
from infra.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/bookings", tags=["checkin"])


class CheckinRequest(BaseModel):
    qr_token: str | None = None
    simulate: bool = False


@router.post("/{id}/checkin", status_code=200)
async def checkin(
    id: UUID,
    payload: CheckinRequest | None = None,
    qr_token: str | None = Query(default=None),
    simulate: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/bookings/{id}/checkin — Confirmação via QR."""
    token = (payload.qr_token if payload and payload.qr_token else None) or qr_token
    is_simulation = (payload.simulate if payload else False) or simulate
    if not token:
        raise HTTPException(status_code=400, detail="qr_token is required")
    try:
        claims = verify_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired check-in token") from exc
    if claims.get("sub") != str(id) or claims.get("purpose") != "booking-checkin":
        raise HTTPException(status_code=401, detail="Token does not belong to this booking")

    booking_repo = BookingRepositoryPostgres(db)
    target_booking = await booking_repo.get_by_id(id)
    if target_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    checkin_time = target_booking.slot.start if is_simulation else datetime.now(UTC)

    try:
        await ConfirmBookingUseCase(
            booking_repo,
            WorkspaceRepositoryPostgres(db),
            AuditLogRepositoryPostgres(db),
            SqlAlchemyUnitOfWork(db),
            event_bus=event_bus,
        ).execute(id, checkin_time)
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CheckInError as exc:
        msg = str(exc)
        if "outside the allowed time window" in msg:
            detail = "O check-in só é permitido entre 10 minutos antes e 10 minutos após o início da reserva."
        elif "Only pending bookings" in msg:
            detail = "Apenas reservas pendentes podem realizar check-in."
        else:
            detail = msg
        raise HTTPException(status_code=409, detail=detail) from exc

    await sse_publisher.publish({"type": "booking.confirmed", "booking_id": str(id)})
    return {"booking_id": str(id), "status": "CONFIRMED", "message": "Check-in validado com sucesso"}


@router.get("/{id}/qr", responses={200: {"content": {"image/png": {}}}})
async def get_booking_qr_code(
    id: UUID,
    current_user: Annotated[dict, Depends(require_auth)],
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/bookings/{id}/qr — Gera imagem PNG do QR Code."""
    booking = await BookingRepositoryPostgres(db).get_by_id(id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    require_booking_owner(current_user, booking.employee_id)
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=400, detail="QR Code is only available for pending bookings")

    now = datetime.now(UTC)
    start = booking.slot.start
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    token_expiry = max(timedelta(minutes=10), start - now + timedelta(minutes=15))
    token = create_access_token(
        {"sub": str(id), "purpose": "booking-checkin"},
        expires_delta=token_expiry,
    )
    png_bytes = generate_qr_png_bytes(token)
    return Response(content=png_bytes, media_type="image/png", headers={"X-Checkin-Token": token})


@router.get("/{id}/checkin-token")
async def get_booking_checkin_token(
    id: UUID,
    current_user: Annotated[dict, Depends(require_auth)],
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/bookings/{id}/checkin-token — Obter token JWT de check-in."""
    booking = await BookingRepositoryPostgres(db).get_by_id(id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    require_booking_owner(current_user, booking.employee_id)
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=400, detail="Check-in token is only available for pending bookings")

    now = datetime.now(UTC)
    start = booking.slot.start
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    token_expiry = max(timedelta(minutes=10), start - now + timedelta(minutes=15))
    token = create_access_token(
        {"sub": str(id), "purpose": "booking-checkin"},
        expires_delta=token_expiry,
    )
    return {"booking_id": str(id), "qr_token": token}
