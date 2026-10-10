from domain.entities.holiday import Holiday
from domain.repositories.availability_window_repository import AvailabilityWindowRepository
from domain.repositories.holiday_repository import HolidayRepository
from domain.repositories.unit_of_work import UnitOfWork


class BlockHolidaysUseCase:
    """UC17: Bloquear Feriados."""

    def __init__(
        self,
        window_repo: AvailabilityWindowRepository,
        holiday_repo: HolidayRepository,
        unit_of_work: UnitOfWork,
    ):
        self.window_repo = window_repo
        self.holiday_repo = holiday_repo
        self.unit_of_work = unit_of_work

    async def execute(self, holiday: Holiday) -> Holiday:
        async with self.unit_of_work.transaction():
            saved = await self.holiday_repo.save(holiday)
            await self.window_repo.delete_by_day(holiday.day.isoformat())
            return saved
