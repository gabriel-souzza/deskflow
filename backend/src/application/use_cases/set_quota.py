from dataclasses import replace
from datetime import date
from decimal import Decimal
from uuid import UUID

from domain.entities.quota_period import QuotaExceededError, QuotaPeriod
from domain.repositories.quota_repository import QuotaRepository
from domain.repositories.unit_of_work import UnitOfWork


class SetQuotaUseCase:
    """UC11: Configurar Cotas."""

    def __init__(self, quota_repo: QuotaRepository, unit_of_work: UnitOfWork):
        self.quota_repo = quota_repo
        self.unit_of_work = unit_of_work

    async def execute(
        self, cost_center_id: UUID, total_hours: Decimal, period_start: date, period_end: date
    ) -> QuotaPeriod:
        async with self.unit_of_work.transaction():
            current = await self.quota_repo.get_for_period(cost_center_id, period_start.isoformat())
            if total_hours < current.consumed_hours:
                raise QuotaExceededError("Quota cannot be set below hours already consumed")
            updated = replace(
                current,
                period_start=period_start,
                period_end=period_end,
                total_hours=total_hours,
            )
            return await self.quota_repo.save(updated)
