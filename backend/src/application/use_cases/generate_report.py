from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from domain.entities.booking import BookingStatus
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.workspace_repository import WorkspaceRepository


class GenerateReportUseCase:
    """UC13/UC14: Dashboard e Exportação."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        workspace_repo: WorkspaceRepository,
    ):
        self.booking_repo = booking_repo
        self.workspace_repo = workspace_repo

    async def execute(self, start_day: date, end_day: date) -> dict[str, Any]:
        if end_day < start_day:
            raise ValueError("Report end date must not precede start date")

        start = datetime.combine(start_day, time.min, tzinfo=UTC)
        end = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=UTC)
        bookings = await self.booking_repo.list_between(start, end)
        workspaces = {
            workspace.id: workspace for workspace in await self.workspace_repo.list_all_active()
        }
        days = (end_day - start_day).days + 1
        total_slot_seats = sum(workspace.capacity for workspace in workspaces.values()) * 40 * days
        occupied_slot_seats = 0
        confirmed_count = 0
        cost_center_hours: dict[str, Decimal] = {}
        by_floor: dict[str, dict[str, int]] = {}
        by_zone: dict[str, dict[str, int]] = {}
        rows = []

        for booking in bookings:
            workspace = workspaces.get(booking.workspace_id)
            if workspace is None:
                continue
            row = {
                "booking_id": str(booking.id),
                "workspace_id": str(workspace.id),
                "workspace_code": workspace.code,
                "floor": workspace.floor,
                "zone": workspace.zone,
                "employee_id": str(booking.employee_id),
                "cost_center_id": str(booking.cost_center_id),
                "slot_start": booking.slot.start.isoformat(),
                "slot_end": booking.slot.end.isoformat(),
                "status": booking.status.value,
            }
            rows.append(row)

            if booking.status is not BookingStatus.CANCELLED:
                duration = booking.duration_hours
                cost_center_hours[row["cost_center_id"]] = (
                    cost_center_hours.get(row["cost_center_id"], Decimal(0)) + duration
                )
            if booking.status is not BookingStatus.CONFIRMED:
                continue

            confirmed_count += 1
            clipped_start = max(booking.slot.start, start)
            clipped_end = min(booking.slot.end, end)
            occupied = int((clipped_end - clipped_start).total_seconds() // 900)
            occupied_slot_seats += occupied
            for dimension, value in ((by_floor, workspace.floor), (by_zone, workspace.zone)):
                summary = dimension.setdefault(
                    value, {"bookings_confirmed": 0, "occupied_slot_seats": 0}
                )
                summary["bookings_confirmed"] += 1
                summary["occupied_slot_seats"] += occupied

        return {
            "start_date": start_day.isoformat(),
            "end_date": end_day.isoformat(),
            "summary": {
                "period": start_day.isoformat()
                if start_day == end_day
                else f"{start_day}/{end_day}",
                "occupancy_rate": round(occupied_slot_seats / total_slot_seats, 4)
                if total_slot_seats
                else 0,
                "bookings_confirmed": confirmed_count,
                "occupied_slot_seats": occupied_slot_seats,
                "total_slot_seats": total_slot_seats,
                "available_spots": max(0, total_slot_seats - occupied_slot_seats),
            },
            "by_floor": by_floor,
            "by_zone": by_zone,
            "cost_center_hours": cost_center_hours,
            "bookings": rows,
        }
