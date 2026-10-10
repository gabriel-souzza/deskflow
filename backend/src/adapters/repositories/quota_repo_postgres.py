from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.quota_period import QuotaPeriod
from domain.repositories.quota_repository import QuotaRepository
from infra.models import CostCenterORM, QuotaPeriodORM


class QuotaRepositoryPostgres(QuotaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_period(self, cost_center_id: UUID, day: str) -> QuotaPeriod:
        requested_day = date.fromisoformat(day)
        period_start = requested_day.replace(day=1)
        next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        period_end = next_month - timedelta(days=1)
        center = await self.session.scalar(
            select(CostCenterORM).where(CostCenterORM.id == cost_center_id).with_for_update()
        )
        if center is None:
            raise LookupError("Cost center not found")
        result = await self.session.execute(
            select(QuotaPeriodORM)
            .where(
                QuotaPeriodORM.cost_center_id == cost_center_id,
                QuotaPeriodORM.period_start == datetime.combine(period_start, time.min),
            )
            .with_for_update()
        )
        row = result.scalars().first()
        if not row:
            return QuotaPeriod(
                cost_center_id=cost_center_id,
                period_start=period_start,
                period_end=period_end,
                total_hours=Decimal(str(center.monthly_quota_hours or 0)),
            )
        return QuotaPeriod(
            cost_center_id=row.cost_center_id,
            period_start=row.period_start.date(),
            period_end=row.period_end.date(),
            total_hours=Decimal(str(row.total_hours)),
            consumed_hours=Decimal(str(row.consumed_hours)),
        )

    async def save(self, quota: QuotaPeriod) -> QuotaPeriod:
        period_start = datetime.combine(quota.period_start, time.min)
        period_end = datetime.combine(quota.period_end, time.min)
        orm = await self.session.get(
            QuotaPeriodORM,
            (quota.cost_center_id, period_start, period_end),
        )
        if orm is None:
            orm = QuotaPeriodORM(
                cost_center_id=quota.cost_center_id,
                period_start=period_start,
                period_end=period_end,
                total_hours=quota.total_hours,
                consumed_hours=quota.consumed_hours,
            )
            self.session.add(orm)
        else:
            orm.total_hours = quota.total_hours
            orm.consumed_hours = quota.consumed_hours
        center = await self.session.get(CostCenterORM, quota.cost_center_id)
        if center is not None:
            center.monthly_quota_hours = quota.total_hours
        await self.session.flush()
        return quota
