import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_admin
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.generate_report import GenerateReportUseCase
from infra.database import get_db
from infra.models import CostCenterORM, EmployeeORM

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _generate_report(db: AsyncSession) -> GenerateReportUseCase:
    return GenerateReportUseCase(BookingRepositoryPostgres(db), WorkspaceRepositoryPostgres(db))


def _format_datetime_str(dt_str: str) -> str:
    try:
        clean = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return dt_str.replace("T", " ")[:16]


def _build_pdf_report(
    report: dict[str, Any],
    employee_map: dict[str, str],
    cost_center_map: dict[str, str],
    start_date: date,
    end_date: date,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=5,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )
    cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
    )
    cell_header = ParagraphStyle(
        "TableHeader",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    story = []
    story.append(Paragraph("DeskFlow — Gestão Inteligente de Espaços Híbridos", title_style))
    story.append(
        Paragraph("Relatório Gerencial de Ocupação, Ociosidade e Rateio de Custos", subtitle_style)
    )
    story.append(Spacer(1, 4))

    start_fmt = start_date.strftime("%d/%m/%Y")
    end_fmt = end_date.strftime("%d/%m/%Y")
    now_fmt = datetime.now().strftime("%d/%m/%Y às %H:%M")
    period_label = start_fmt if start_date == end_date else f"{start_fmt} a {end_fmt}"
    story.append(
        Paragraph(
            f"<b>Período Analisado:</b> {period_label} &nbsp;|&nbsp; <b>Emitido em:</b> {now_fmt}",
            meta_style,
        )
    )
    story.append(Spacer(1, 10))

    summary = report.get("summary", {})
    occupancy_rate = summary.get("utilization_rate", summary.get("occupancy_rate", 0))
    no_show_rate = summary.get("no_show_rate", 0)
    confirmed = summary.get("bookings_confirmed", 0)
    expired = summary.get("bookings_expired", 0)
    pending = summary.get("bookings_pending", 0)
    total_hours = sum(Decimal(str(h)) for h in report.get("cost_center_hours", {}).values())
    total_stations = summary.get("total_stations", 0)
    total_rooms = summary.get("total_meeting_rooms", 0)

    kpi_data = [
        [
            Paragraph(
                f"<b>Taxa de Ocupação</b><br/><font size=15 color='#2563eb'><b>{(occupancy_rate * 100):.1f}%</b></font><br/><font size=7 color='#64748b'>{confirmed} confirmada(s) &bull; {pending} pendente(s)</font>",
                styles["Normal"],
            ),
            Paragraph(
                f"<b>Taxa de No-Show</b><br/><font size=15 color='#d97706'><b>{(no_show_rate * 100):.1f}%</b></font><br/><font size=7 color='#64748b'>{expired} expirada(s) por tolerância</font>",
                styles["Normal"],
            ),
            Paragraph(
                f"<b>Total de Horas</b><br/><font size=15 color='#0f172a'><b>{total_hours:.1f}h</b></font><br/><font size=7 color='#64748b'>Alocadas para departamentos</font>",
                styles["Normal"],
            ),
            Paragraph(
                f"<b>Espaços Disponíveis</b><br/><font size=15 color='#0f172a'><b>{total_stations + total_rooms}</b></font><br/><font size=7 color='#64748b'>{total_stations} estações &bull; {total_rooms} salas</font>",
                styles["Normal"],
            ),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[180, 180, 180, 180])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (0, 0), 0.75, colors.HexColor("#e2e8f0")),
                ("BOX", (1, 0), (1, 0), 0.75, colors.HexColor("#e2e8f0")),
                ("BOX", (2, 0), (2, 0), 0.75, colors.HexColor("#e2e8f0")),
                ("BOX", (3, 0), (3, 0), 0.75, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Rateio de Horas por Centro de Custo", section_style))
    cc_hours_dict = report.get("cost_center_hours", {})
    if cc_hours_dict:
        cc_table_rows = [
            [
                Paragraph("Centro de Custo", cell_header),
                Paragraph("Horas Consumidas", cell_header),
                Paragraph("Participação no Período", cell_header),
            ]
        ]
        total_cc_hours = float(total_hours) if total_hours > 0 else 1.0
        for cc_id, h in cc_hours_dict.items():
            cc_name = cost_center_map.get(str(cc_id), str(cc_id))
            h_float = float(h)
            pct = (h_float / total_cc_hours * 100) if total_hours > 0 else 0
            cc_table_rows.append(
                [
                    Paragraph(cc_name, cell_style),
                    Paragraph(f"{h_float:.1f}h", cell_style),
                    Paragraph(f"{pct:.1f}%", cell_style),
                ]
            )
        cc_table_rows.append(
            [
                Paragraph("<b>TOTAL GERAL</b>", cell_bold),
                Paragraph(f"<b>{total_hours:.1f}h</b>", cell_bold),
                Paragraph("<b>100%</b>", cell_bold),
            ]
        )
        cc_table = Table(cc_table_rows, colWidths=[360, 180, 180])
        cc_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
                ]
            )
        )
        story.append(cc_table)
    else:
        empty_cc = Table(
            [[Paragraph("<font color='#64748b'>Nenhum consumo de cotas registrado para o período.</font>", cell_style)]],
            colWidths=[720],
        )
        empty_cc.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(empty_cc)

    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Detalhamento das Reservas", section_style))
    bookings = report.get("bookings", [])
    if bookings:
        b_rows = [
            [
                Paragraph("Espaço", cell_header),
                Paragraph("Localização", cell_header),
                Paragraph("Colaborador", cell_header),
                Paragraph("Centro de Custo", cell_header),
                Paragraph("Início", cell_header),
                Paragraph("Fim", cell_header),
                Paragraph("Duração", cell_header),
                Paragraph("Status", cell_header),
            ]
        ]
        status_map = {
            "CONFIRMED": ("Confirmada", "#059669"),
            "PENDING": ("Pendente", "#d97706"),
            "CANCELLED": ("Cancelada", "#64748b"),
            "EXPIRED": ("Expirada", "#dc2626"),
        }
        for b in bookings:
            emp = employee_map.get(str(b.get("employee_id")), str(b.get("employee_id", "N/A")))
            cc = cost_center_map.get(str(b.get("cost_center_id")), str(b.get("cost_center_id", "N/A")))
            st_text, st_color = status_map.get(b.get("status", ""), (b.get("status", ""), "#475569"))

            s_start = _format_datetime_str(b.get("slot_start", ""))
            s_end = _format_datetime_str(b.get("slot_end", ""))

            try:
                dt_s = datetime.fromisoformat(b.get("slot_start", "").replace("Z", "+00:00"))
                dt_e = datetime.fromisoformat(b.get("slot_end", "").replace("Z", "+00:00"))
                dur_h = (dt_e - dt_s).total_seconds() / 3600
                dur_str = f"{dur_h:.1f}h"
            except Exception:
                dur_str = "-"

            b_rows.append(
                [
                    Paragraph(b.get("workspace_code", "N/A"), cell_bold),
                    Paragraph(f"{b.get('floor', '')}º Andar ({b.get('zone', '')})", cell_style),
                    Paragraph(emp, cell_style),
                    Paragraph(cc, cell_style),
                    Paragraph(s_start, cell_style),
                    Paragraph(s_end, cell_style),
                    Paragraph(dur_str, cell_style),
                    Paragraph(f"<font color='{st_color}'><b>{st_text}</b></font>", cell_style),
                ]
            )
        b_table = Table(b_rows, colWidths=[60, 95, 175, 110, 95, 95, 45, 45], repeatRows=1)
        b_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(b_table)
    else:
        empty_box = [
            [
                Paragraph(
                    f"<b>Nenhuma reserva registrada para o período selecionado ({period_label}).</b><br/><br/>"
                    f"<font color='#64748b'>Não foram encontrados agendamentos confirmados, pendentes ou expirados neste intervalo.<br/>"
                    f"Para visualizar dados históricos ou futuros, ajuste os filtros de data no painel de relatórios.</font>",
                    styles["Normal"],
                )
            ]
        ]
        empty_table = Table(empty_box, colWidths=[720])
        empty_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 16),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(empty_table)

    doc.build(story)
    return buffer.getvalue()


@router.get("/utilization")
async def utilization(
    day: date | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/reports/utilization — Dashboard."""
    target_start = start_date or day or date.today()
    target_end = end_date or day or target_start
    if target_end < target_start:
        raise HTTPException(status_code=422, detail="end_date must not precede start_date")
    try:
        report = await _generate_report(db).execute(target_start, target_end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    cost_centers_rows = (await db.execute(select(CostCenterORM.id, CostCenterORM.name))).all()
    cost_center_names = {str(row.id): row.name for row in cost_centers_rows}

    return {
        **report["summary"],
        "summary": report["summary"],
        "by_floor": report["by_floor"],
        "by_zone": report["by_zone"],
        "cost_center_hours": {k: float(v) for k, v in report["cost_center_hours"].items()},
        "cost_center_names": cost_center_names,
    }


@router.get("/export")
async def export_report(
    start_date: date = Query(default_factory=date.today),
    end_date: date = Query(default_factory=date.today),
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/reports/export — CSV/PDF."""
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must not precede start_date")
    report = await _generate_report(db).execute(start_date, end_date)

    employees_rows = (
        await db.execute(select(EmployeeORM.id, EmployeeORM.name, EmployeeORM.email))
    ).all()
    cost_centers_rows = (
        await db.execute(select(CostCenterORM.id, CostCenterORM.name))
    ).all()

    employee_map = {str(row.id): f"{row.name} ({row.email})" for row in employees_rows}
    cost_center_map = {str(row.id): row.name for row in cost_centers_rows}

    filename = f"deskflow-relatorio-{start_date.isoformat()}-{end_date.isoformat()}"
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "booking_id",
                "workspace_code",
                "floor",
                "zone",
                "employee_id",
                "employee_name",
                "cost_center_id",
                "cost_center_name",
                "start",
                "end",
                "status",
            ]
        )
        for booking in report["bookings"]:
            emp_str = employee_map.get(booking["employee_id"], "")
            cc_str = cost_center_map.get(booking["cost_center_id"], "")
            writer.writerow(
                [
                    booking["booking_id"],
                    booking["workspace_code"],
                    booking["floor"],
                    booking["zone"],
                    booking["employee_id"],
                    emp_str,
                    booking["cost_center_id"],
                    cc_str,
                    booking["slot_start"],
                    booking["slot_end"],
                    booking["status"],
                ]
            )
        writer.writerow([])
        writer.writerow(["--- RESUMO POR CENTRO DE CUSTO ---"])
        writer.writerow(["cost_center_id", "cost_center_name", "total_hours"])
        for cc_id, hours in report["cost_center_hours"].items():
            writer.writerow([cc_id, cost_center_map.get(cc_id, cc_id), str(hours)])

        csv_content = output.getvalue()
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )

    pdf_bytes = _build_pdf_report(report, employee_map, cost_center_map, start_date, end_date)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )
