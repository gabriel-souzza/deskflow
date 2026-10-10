from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.events.sse_publisher import sse_publisher
from adapters.repositories.audit_log_repo_postgres import AuditLogRepositoryPostgres
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.confirm_booking import (
    BookingNotFoundError,
    CheckInError,
    ConfirmBookingUseCase,
)
from infra.database import get_db
from infra.security import verify_token
from infra.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/bookings", tags=["checkin"])


@router.post("/{id}/checkin", status_code=200)
async def checkin(id: UUID, qr_token: str, db: AsyncSession = Depends(get_db)):
    """POST /api/v1/bookings/{id}/checkin — Confirmação via QR (UC06, I4)."""
    if not qr_token:
        raise HTTPException(status_code=400, detail="qr_token is required")
    try:
        claims = verify_token(qr_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired check-in token") from exc
    if claims.get("sub") != str(id) or claims.get("purpose") != "booking-checkin":
        raise HTTPException(status_code=401, detail="Token does not belong to this booking")

    try:
        booking = await ConfirmBookingUseCase(
            BookingRepositoryPostgres(db),
            WorkspaceRepositoryPostgres(db),
            AuditLogRepositoryPostgres(db),
            SqlAlchemyUnitOfWork(db),
        ).execute(id, datetime.now(UTC))
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CheckInError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await sse_publisher.publish({"type": "booking.confirmed", "booking_id": str(id)})
    return {"booking_id": str(id), "status": "CONFIRMED", "message": "Check-in validated"}
