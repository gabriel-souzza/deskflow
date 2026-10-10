from datetime import date
from decimal import Decimal
from uuid import uuid4

from domain.entities.quota_period import QuotaExceededError, QuotaPeriod


def test_quota_consume_ok():
    qp = QuotaPeriod(cost_center_id=uuid4(), period_start=date(2026,9,1), period_end=date(2026,9,30), total_hours=Decimal(100))
    result = qp.consume(Decimal(10))
    assert result.consumed_hours == Decimal(10)

def test_quota_exceeds():
    qp = QuotaPeriod(cost_center_id=uuid4(), period_start=date(2026,9,1), period_end=date(2026,9,30), total_hours=Decimal(10))
    try:
        qp.consume(Decimal(11))
        assert False
    except QuotaExceededError:
        pass