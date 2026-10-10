from datetime import date, datetime, time, timedelta
from uuid import UUID

from domain.entities.workspace import Workspace, WorkspaceType
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.holiday_repository import HolidayRepository
from domain.repositories.workspace_repository import WorkspaceRepository


class GetAvailabilityUseCase:
    """UC01: Consultar Disponibilidade por workspace, dia e filtros (andar/zona/tipo)."""

    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        booking_repo: BookingRepository,
        holiday_repo: HolidayRepository | None = None,
    ):
        self.workspace_repo = workspace_repo
        self.booking_repo = booking_repo
        self.holiday_repo = holiday_repo

    async def execute(
        self,
        day: date,
        workspace_id: UUID | None = None,
        floor: str | None = None,
        zone: str | None = None,
        workspace_type: WorkspaceType | None = None,
    ) -> dict:
        if self.holiday_repo and await self.holiday_repo.is_blocked(day):
            return {
                "day": day.isoformat(),
                "is_holiday": True,
                "workspaces": [],
            }

        all_workspaces = await self.workspace_repo.list_all_active()
        filtered: list[Workspace] = []
        for ws in all_workspaces:
            if workspace_id is not None and ws.id != workspace_id:
                continue
            if floor is not None and ws.floor != floor:
                continue
            if zone is not None and ws.zone != zone:
                continue
            if workspace_type is not None and ws.type != workspace_type:
                continue
            filtered.append(ws)

        day_key = day.isoformat()
        day_start = datetime.combine(day, time(8))
        result_workspaces = []

        for ws in filtered:
            slots = []
            for slot_index in range(40):
                start = day_start + timedelta(minutes=15 * slot_index)
                end = start + timedelta(minutes=15)
                occupied = await self.booking_repo.count_by_window(ws.id, day_key, slot_index)
                seats_available = max(0, ws.capacity - occupied)
                slots.append(
                    {
                        "slot_index": slot_index,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "capacity": ws.capacity,
                        "seats_available": seats_available,
                    }
                )
            result_workspaces.append(
                {
                    "workspace_id": str(ws.id),
                    "code": ws.code,
                    "floor": ws.floor,
                    "zone": ws.zone,
                    "type": ws.type.value,
                    "capacity": ws.capacity,
                    "slots": slots,
                }
            )

        return {
            "day": day.isoformat(),
            "is_holiday": False,
            "workspaces": result_workspaces,
        }
