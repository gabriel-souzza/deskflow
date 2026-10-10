from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.post("/{id}/checkin", status_code=200)
async def checkin(
    id: UUID,
    payload: CheckinRequest | None = None,
    qr_token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/bookings/{id}/checkin — Confirmação via QR (UC06, I4)."""
    token = (payload.qr_token if payload and payload.qr_token else None) or qr_token
    if not token:
        raise HTTPException(status_code=400, detail="qr_token is required")
    try:
        claims = verify_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired check-in token") from exc
    if claims.get("sub") != str(id) or claims.get("purpose") != "booking-checkin":
        raise HTTPException(status_code=401, detail="Token does not belong to this booking")

    try:
        await ConfirmBookingUseCase(
            BookingRepositoryPostgres(db),
            WorkspaceRepositoryPostgres(db),
            AuditLogRepositoryPostgres(db),
            SqlAlchemyUnitOfWork(db),
            event_bus=event_bus,
        ).execute(id, datetime.now(UTC))
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CheckInError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await sse_publisher.publish({"type": "booking.confirmed", "booking_id": str(id)})
    return {"booking_id": str(id), "status": "CONFIRMED", "message": "Check-in validated"}


@router.get("/{id}/qr", responses={200: {"content": {"image/png": {}}}})
async def get_booking_qr_code(
    id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/bookings/{id}/qr — Gera imagem PNG do QR Code (UC06, RF02)."""
    booking = await BookingRepositoryPostgres(db).get_by_id(id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
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
    return Response(content=png_bytes, media_type="image/png")
