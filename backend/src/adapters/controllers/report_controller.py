import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_admin
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.generate_report import GenerateReportUseCase
from infra.database import get_db

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _generate_report(db: AsyncSession) -> GenerateReportUseCase:
    return GenerateReportUseCase(BookingRepositoryPostgres(db), WorkspaceRepositoryPostgres(db))


@router.get("/utilization")
async def utilization(
    day: date = Query(default_factory=date.today),
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/reports/utilization — Dashboard (UC13)."""
    try:
        report = await _generate_report(db).execute(day, day)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return report["summary"]


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
    report = await _generate_report(db).execute(start_date, end_date)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["booking_id", "workspace_code", "floor", "zone", "employee_id", "start", "end", "status"]
    )
    for booking in report["bookings"]:
        writer.writerow(
            [
                booking["booking_id"],
                booking["workspace_code"],
                booking["floor"],
                booking["zone"],
                booking["employee_id"],
                booking["slot_start"],
                booking["slot_end"],
                booking["status"],
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
