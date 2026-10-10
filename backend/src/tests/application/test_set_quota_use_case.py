from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from application.use_cases.set_quota import SetQuotaUseCase
from domain.entities.quota_period import QuotaExceededError, QuotaPeriod


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeQuotaRepository:
    def __init__(self, quota):
        self.quota = quota
        self.saved = []

    async def get_for_period(self, _cost_center_id, _day):
        return self.quota

    async def save(self, quota):
        self.quota = quota
        self.saved.append(quota)
        return quota


@pytest.mark.asyncio
async def test_set_quota_preserves_consumption_and_updates_limit():
    center_id = uuid4()
    existing = QuotaPeriod(
        cost_center_id=center_id,
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        total_hours=Decimal(40),
        consumed_hours=Decimal(12),
    )
    repository = FakeQuotaRepository(existing)
    use_case = SetQuotaUseCase(repository, FakeUnitOfWork())

    updated = await use_case.execute(center_id, Decimal(50), date(2026, 10, 1), date(2026, 10, 31))

    assert updated.total_hours == Decimal(50)
    assert updated.consumed_hours == Decimal(12)
    assert repository.saved == [updated]


@pytest.mark.asyncio
async def test_set_quota_rejects_limit_below_consumption():
    center_id = uuid4()
    existing = QuotaPeriod(
        cost_center_id=center_id,
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        total_hours=Decimal(40),
        consumed_hours=Decimal(12),
    )
    repository = FakeQuotaRepository(existing)
    use_case = SetQuotaUseCase(repository, FakeUnitOfWork())

    with pytest.raises(QuotaExceededError):
        await use_case.execute(center_id, Decimal(10), date(2026, 10, 1), date(2026, 10, 31))

    assert repository.saved == []
