from domain.repositories.availability_window_repository import AvailabilityWindowRepository


class GenerateDailyAvailabilityUseCase:
    """UC16: Gerar Disponibilidade Diária (08:00-18:00, grid 15min)."""

    def __init__(self, window_repo: AvailabilityWindowRepository):
        self.window_repo = window_repo

    async def execute(self, day: str) -> None:
        pass