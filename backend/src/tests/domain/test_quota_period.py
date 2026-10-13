from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.entities.quota_period import QuotaExceededError, QuotaPeriod


def test_quota_consume_ok():
    qp = QuotaPeriod(
        cost_center_id=uuid4(),
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        total_hours=Decimal(100),
    )
    result = qp.consume(Decimal(10))
    assert result.consumed_hours == Decimal(10)
    assert result.remaining_hours() == Decimal(90)
    assert result.can_consume(Decimal(90)) is True
    assert result.can_consume(Decimal(91)) is False


def test_quota_exceeds():
    qp = QuotaPeriod(
        cost_center_id=uuid4(),
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        total_hours=Decimal(10),
    )
    with pytest.raises(QuotaExceededError, match="Insufficient quota"):
        qp.consume(Decimal(11))


def test_quota_refund_ok():
    qp = QuotaPeriod(
        cost_center_id=uuid4(),
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        total_hours=Decimal(50),
        consumed_hours=Decimal(20),
    )
    refunded = qp.consume(Decimal(-5))
    assert refunded.consumed_hours == Decimal(15)


def test_quota_refund_more_than_consumed_raises():
    qp = QuotaPeriod(
        cost_center_id=uuid4(),
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        total_hours=Decimal(50),
        consumed_hours=Decimal(5),
    )
    with pytest.raises(ValueError, match="Cannot refund more than consumed"):
        qp.consume(Decimal(-10))


def test_quota_period_validation_errors():
    cc_id = uuid4()
    start = date(2026, 9, 1)
    end = date(2026, 9, 30)

    with pytest.raises(ValueError, match="cost_center_id is required"):
        QuotaPeriod(cost_center_id=None, period_start=start, period_end=end)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="period_start and period_end are required"):
        QuotaPeriod(cost_center_id=cc_id, period_start=None, period_end=end)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="period_start must be <= period_end"):
        QuotaPeriod(cost_center_id=cc_id, period_start=end, period_end=start)

    with pytest.raises(ValueError, match="total_hours cannot be negative"):
        QuotaPeriod(cost_center_id=cc_id, period_start=start, period_end=end, total_hours=Decimal(-1))

    with pytest.raises(ValueError, match="consumed_hours cannot be negative"):
        QuotaPeriod(cost_center_id=cc_id, period_start=start, period_end=end, consumed_hours=Decimal(-1))

    with pytest.raises(QuotaExceededError, match="exceed total"):
        QuotaPeriod(
            cost_center_id=cc_id,
            period_start=start,
            period_end=end,
            total_hours=Decimal(10),
            consumed_hours=Decimal(15),
        )