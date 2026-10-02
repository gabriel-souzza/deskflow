from domain.entities.holiday import Holiday
from domain.repositories.availability_window_repository import AvailabilityWindowRepository


class BlockHolidaysUseCase:
    """UC17: Bloquear Feriados."""

    def __init__(self, window_repo: AvailabilityWindowRepository):
        self.window_repo = window_repo

    async def execute(self, holiday: Holiday) -> None:
        pass