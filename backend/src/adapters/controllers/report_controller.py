import csv
import io
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.admin_controller import require_admin
from infra.database import get_db
from infra.models import BookingORM, WorkspaceORM

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


async def _report_rows(db: AsyncSession, start: datetime, end: datetime):
    result = await db.execute(
        select(BookingORM, WorkspaceORM)
        .join(WorkspaceORM, WorkspaceORM.id == BookingORM.workspace_id)
        .where(
            BookingORM.slot_start < end,
            BookingORM.slot_end > start,
        )
        .order_by(BookingORM.slot_start)
    )
    return result.all()


@router.get("/utilization")
async def utilization(
    day: date = Query(default_factory=date.today),
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/reports/utilization — Dashboard (UC13)."""
    start = datetime.combine(day, time(8))
    end = datetime.combine(day, time(18))
    rows = await _report_rows(db, start, end)
    workspace_result = await db.execute(select(WorkspaceORM))
    total_capacity = sum(item.capacity for item in workspace_result.scalars().all()) * 40
    occupied_slot_seats = 0
    confirmed_count = 0
    for booking, _workspace in rows:
        if booking.status != "CONFIRMED":
            continue
        confirmed_count += 1
        clipped_start = max(booking.slot_start, start)
        clipped_end = min(booking.slot_end, end)
        occupied_slot_seats += int((clipped_end - clipped_start).total_seconds() // 900)
    return {
        "period": day.isoformat(),
        "occupancy_rate": round(occupied_slot_seats / total_capacity, 4) if total_capacity else 0,
        "bookings_confirmed": confirmed_count,
        "available_spots": max(0, total_capacity - occupied_slot_seats),
    }


@router.get("/export")
async def export_report(
    start_date: date = Query(default_factory=date.today),
    end_date: date = Query(default_factory=date.today),
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/reports/export — CSV/PDF (UC14)."""
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must not precede start_date")
    start = datetime.combine(start_date, time.min)
    end = datetime.combine(end_date + timedelta(days=1), time.min)
    rows = await _report_rows(db, start, end)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["booking_id", "workspace_code", "floor", "zone", "employee_id", "start", "end", "status"]
    )
    for booking, workspace in rows:
        writer.writerow(
            [
                str(booking.id),
                workspace.code,
                workspace.floor,
                workspace.zone,
                str(booking.employee_id),
                booking.slot_start.isoformat(),
                booking.slot_end.isoformat(),
                booking.status,
            ]
        )
    csv_content = output.getvalue()
    filename = f"deskflow-report-{start_date.isoformat()}-{end_date.isoformat()}"
    if format == "csv":
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )

    pdf = io.BytesIO()
    page = canvas.Canvas(pdf, pagesize=landscape(letter))
    page.drawString(36, 560, f"DeskFlow bookings: {start_date} to {end_date}")
    y = 530
    for line in csv_content.splitlines()[:35]:
        page.drawString(36, y, line[:150])
        y -= 14
        if y < 36:
            page.showPage()
            y = 560
    page.save()
    return Response(
        content=pdf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )
