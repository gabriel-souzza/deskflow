from domain.repositories.booking_repository import BookingRepository
from domain.repositories.workspace_repository import WorkspaceRepository
from domain.repositories.quota_repository import QuotaRepository


class GenerateReportUseCase:
    """UC13/UC14: Dashboard e Exportação."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        workspace_repo: WorkspaceRepository,
        quota_repo: QuotaRepository,
    ):
        self.booking_repo = booking_repo
        self.workspace_repo = workspace_repo
        self.quota_repo = quota_repo

    async def execute(self, period: str) -> dict:
        return {"message": "Report not fully implemented", "period": period}