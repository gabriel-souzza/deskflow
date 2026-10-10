from datetime import date

from domain.entities.availability_window import AvailabilityWindow
from domain.repositories.availability_window_repository import AvailabilityWindowRepository
from domain.repositories.holiday_repository import HolidayRepository
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.workspace_repository import WorkspaceRepository
from domain.value_objects.capacity import Capacity


class GenerateDailyAvailabilityUseCase:
    """UC16: Gerar Disponibilidade Diária (08:00-18:00, grid 15min)."""

    def __init__(
        self,
        window_repo: AvailabilityWindowRepository,
        workspace_repo: WorkspaceRepository,
        holiday_repo: HolidayRepository,
        unit_of_work: UnitOfWork,
    ):
        self.window_repo = window_repo
        self.workspace_repo = workspace_repo
        self.holiday_repo = holiday_repo
        self.unit_of_work = unit_of_work

    async def execute(self, day: str) -> int:
        requested_day = date.fromisoformat(day)
        async with self.unit_of_work.transaction():
            if await self.holiday_repo.is_blocked(requested_day):
                return 0

            created = 0
            for workspace in await self.workspace_repo.list_all_active():
                for slot_index in range(40):
                    if await self.window_repo.get_by_key(workspace.id, day, slot_index):
                        continue
                    await self.window_repo.save(
                        AvailabilityWindow(
                            workspace_id=workspace.id,
                            day=day,
                            slot_index=slot_index,
                            capacity=Capacity(seats=workspace.capacity),
                        )
                    )
                    created += 1
            return created
