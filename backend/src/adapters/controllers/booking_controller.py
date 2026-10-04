from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.events.sse_publisher import sse_publisher
from infra.database import get_db
from infra.models import (
    AuditLogORM,
    BookingORM,
    BookingWindowORM,
    CostCenterORM,
    EmployeeORM,
    QuotaPeriodORM,
    WorkspaceORM,
)
from infra.security import create_access_token

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _slot_indices(start: datetime, end: datetime) -> list[int]:
    indices = []
    current = start
    while current < end:
        indices.append((current.hour * 60 + current.minute - 8 * 60) // 15)
        current += timedelta(minutes=15)
    return indices


@router.post("", status_code=201)
async def create_booking(
    workspace_id: UUID,
    employee_id: UUID,
    cost_center_id: UUID,
    slot_start: datetime,
    slot_end: datetime,
    db: AsyncSession = Depends(get_db),
):
    start = _naive_utc(slot_start)
    end = _naive_utc(slot_end)
    if start >= end or start.date() != end.date():
        raise HTTPException(
            status_code=400, detail="Booking must have a positive duration on one day"
        )
    if start.minute % 15 or end.minute % 15 or start.second or end.second:
        raise HTTPException(status_code=400, detail="Booking times must align to 15-minute slots")
    if start.time() < time(8) or end.time() > time(18):
        raise HTTPException(status_code=409, detail="Booking is outside the 08:00-18:00 window")

    now = datetime.now(UTC).replace(tzinfo=None)
    booking_id = uuid4()
    async with db.begin():
        workspace = await db.scalar(
            select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
        )
        employee = await db.get(EmployeeORM, employee_id)
        cost_center = await db.scalar(
            select(CostCenterORM).where(CostCenterORM.id == cost_center_id).with_for_update()
        )
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if employee is None or cost_center is None:
            raise HTTPException(status_code=404, detail="Employee or cost center not found")
        if employee.cost_center_id != cost_center_id:
            raise HTTPException(
                status_code=422, detail="Employee does not belong to this cost center"
            )
        if not employee.is_eligible_for_booking:
            raise HTTPException(status_code=403, detail="Employee is not eligible to book")

        active_statuses = ("PENDING", "CONFIRMED")
        for slot_index in _slot_indices(start, end):
            slot_start = datetime.combine(start.date(), time(8)) + timedelta(
                minutes=15 * slot_index
            )
            slot_end = slot_start + timedelta(minutes=15)
            occupied = await db.scalar(
                select(func.count(BookingORM.id)).where(
                    BookingORM.workspace_id == workspace_id,
                    BookingORM.status.in_(active_statuses),
                    BookingORM.slot_start < slot_end,
                    BookingORM.slot_end > slot_start,
                )
            )
            if (occupied or 0) >= workspace.capacity:
                raise HTTPException(status_code=409, detail="Workspace capacity is unavailable")

        period_start = datetime(start.year, start.month, 1)
        next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        period_end = next_month - timedelta(days=1)
        quota = await db.scalar(
            select(QuotaPeriodORM)
            .where(
                QuotaPeriodORM.cost_center_id == cost_center_id,
                QuotaPeriodORM.period_start == period_start,
            )
            .with_for_update()
        )
        if quota is None:
            quota = QuotaPeriodORM(
                cost_center_id=cost_center_id,
                period_start=period_start,
                period_end=period_end,
                total_hours=cost_center.monthly_quota_hours or Decimal(0),
                consumed_hours=Decimal(0),
            )
            db.add(quota)
            await db.flush()

        duration = Decimal(str((end - start).total_seconds())) / Decimal(3600)
        if Decimal(str(quota.consumed_hours)) + duration > Decimal(str(quota.total_hours)):
            raise HTTPException(status_code=402, detail="Insufficient cost center quota")
        quota.consumed_hours = Decimal(str(quota.consumed_hours)) + duration

        db.add(
            BookingORM(
                id=booking_id,
                workspace_id=workspace_id,
                employee_id=employee_id,
                cost_center_id=cost_center_id,
                slot_start=start,
                slot_end=end,
                status="PENDING",
                created_at=now,
                modified_at=now,
            )
        )
        for slot_index in _slot_indices(start, end):
            db.add(
                BookingWindowORM(
                    booking_id=booking_id,
                    workspace_id=workspace_id,
                    day=start.date().isoformat(),
                    slot_index=slot_index,
                )
            )
        db.add(
            AuditLogORM(
                actor_id=employee_id,
                action="created",
                entity_type="booking",
                entity_id=str(booking_id),
                timestamp=now,
                reason="booking created",
            )
        )

    checkin_tolerance = 15 if workspace.type == "sala" else 10
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
async def cancel_booking(id: UUID, db: AsyncSession = Depends(get_db)):
    now = datetime.now(UTC).replace(tzinfo=None)
    async with db.begin():
        booking = await db.scalar(select(BookingORM).where(BookingORM.id == id).with_for_update())
        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.status not in ("PENDING", "CONFIRMED"):
            raise HTTPException(
                status_code=409, detail="Booking cannot be cancelled in its current state"
            )
        if booking.slot_start - now < timedelta(hours=2):
            raise HTTPException(
                status_code=409, detail="Cancellation requires at least 2 hours' notice"
            )

        quota = await db.scalar(
            select(QuotaPeriodORM)
            .where(
                QuotaPeriodORM.cost_center_id == booking.cost_center_id,
                QuotaPeriodORM.period_start
                == datetime(booking.slot_start.year, booking.slot_start.month, 1),
            )
            .with_for_update()
        )
        if quota is not None:
            duration = Decimal(
                str((booking.slot_end - booking.slot_start).total_seconds())
            ) / Decimal(3600)
            quota.consumed_hours = max(Decimal(0), Decimal(str(quota.consumed_hours)) - duration)
        await db.execute(delete(BookingWindowORM).where(BookingWindowORM.booking_id == id))
        booking.status = "CANCELLED"
        booking.modified_at = now
        db.add(
            AuditLogORM(
                actor_id=booking.employee_id,
                action="cancelled",
                entity_type="booking",
                entity_id=str(id),
                timestamp=now,
                reason="booking cancelled",
            )
        )

    await sse_publisher.publish({"type": "booking.cancelled", "booking_id": str(id)})
    return {"id": str(id), "status": "CANCELLED"}
