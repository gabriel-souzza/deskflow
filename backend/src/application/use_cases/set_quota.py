from domain.repositories.quota_repository import QuotaRepository
from domain.entities.quota_period import QuotaPeriod
from decimal import Decimal
from uuid import UUID
from datetime import date


class SetQuotaUseCase:
    """UC11: Configurar Cotas."""

    def __init__(self, quota_repo: QuotaRepository):
        self.quota_repo = quota_repo

    async def execute(self, cost_center_id: UUID, total_hours: Decimal, period_start: date, period_end: date) -> QuotaPeriod:
        quota = QuotaPeriod(
            cost_center_id=cost_center_id,
            period_start=period_start,
            period_end=period_end,
            total_hours=total_hours,
            consumed_hours=Decimal("0"),
        )
        await self.quota_repo.save(quota)
        return quota