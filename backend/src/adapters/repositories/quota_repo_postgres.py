from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from domain.repositories.quota_repository import QuotaRepository
from domain.entities.quota_period import QuotaPeriod
from infra.models import QuotaPeriodORM


class QuotaRepositoryPostgres(QuotaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_period(self, cost_center_id: UUID, day: str) -> QuotaPeriod:
        # Simplificado: busca pelo período que contém o dia
        result = await self.session.execute(
            select(QuotaPeriodORM).where(QuotaPeriodORM.cost_center_id == cost_center_id)
        )
        row = result.scalars().first()
        if not row:
            # Cria período default se não existir
            return QuotaPeriod(cost_center_id=cost_center_id, period_start=__import__('datetime').date.today(), period_end=__import__('datetime').date.today(), total_hours=Decimal("100"))
        return QuotaPeriod(
            cost_center_id=row.cost_center_id,
            period_start=row.period_start,
            period_end=row.period_end,
            total_hours=Decimal(str(row.total_hours)),
            consumed_hours=Decimal(str(row.consumed_hours)),
        )

    async def save(self, quota: QuotaPeriod) -> QuotaPeriod:
        orm = QuotaPeriodORM(
            cost_center_id=quota.cost_center_id,
            period_start=quota.period_start,
            period_end=quota.period_end,
            total_hours=float(quota.total_hours),
            consumed_hours=float(quota.consumed_hours),
        )
        self.session.add(orm)
        await self.session.commit()
        return quota