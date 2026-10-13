from datetime import date

import pytest

from domain.entities.holiday import Holiday


def test_holiday_valid_creation():
    h = Holiday(day=date(2026, 12, 25), description="Natal")
    assert h.day == date(2026, 12, 25)
    assert h.description == "Natal"
    assert h.is_blocked() is True


def test_holiday_missing_day():
    with pytest.raises(ValueError, match="day is required"):
        Holiday(day=None)  # type: ignore[arg-type]
