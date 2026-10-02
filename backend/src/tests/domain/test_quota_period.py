from decimal import Decimal
from domain.entities.quota_period import QuotaPeriod, QuotaExceededError
from datetime import date
from uuid import uuid4

def test_quota_consume_ok():
    qp = QuotaPeriod(cost_center_id=uuid4(), period_start=date(2026,9,1), period_end=date(2026,9,30), total_hours=Decimal("100"))
    result = qp.consume(Decimal("10"))
    assert result.consumed_hours == Decimal("10")

def test_quota_exceeds():
    qp = QuotaPeriod(cost_center_id=uuid4(), period_start=date(2026,9,1), period_end=date(2026,9,30), total_hours=Decimal("10"))
    try:
        qp.consume(Decimal("11"))
        assert False
    except QuotaExceededError:
        pass