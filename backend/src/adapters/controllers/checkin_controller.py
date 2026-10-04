from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.events.sse_publisher import sse_publisher
from infra.database import get_db
from infra.models import AuditLogORM, BookingORM, WorkspaceORM
from infra.security import verify_token

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

    now = datetime.now(UTC).replace(tzinfo=None)
    async with db.begin():
        booking = await db.scalar(select(BookingORM).where(BookingORM.id == id).with_for_update())
        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status != "PENDING":
            raise HTTPException(status_code=409, detail="Only pending bookings can be checked in")
        workspace = await db.get(WorkspaceORM, booking.workspace_id)
        tolerance = timedelta(minutes=15 if workspace and workspace.type == "sala" else 10)
        if now < booking.slot_start or now > booking.slot_start + tolerance:
            raise HTTPException(
                status_code=409, detail="Check-in is outside the allowed time window"
            )
        booking.status = "CONFIRMED"
        booking.modified_at = now
        db.add(
            AuditLogORM(
                actor_id=booking.employee_id,
                action="checked_in",
                entity_type="booking",
                entity_id=str(id),
                timestamp=now,
                reason="QR check-in",
            )
        )

    await sse_publisher.publish({"type": "booking.confirmed", "booking_id": str(id)})
    return {"booking_id": str(id), "status": "CONFIRMED", "message": "Check-in validated"}
