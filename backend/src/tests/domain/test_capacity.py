import pytest

from domain.value_objects.capacity import Capacity


def test_capacity_valid():
    c = Capacity(seats=5, zone="Quiet")
    assert c.seats == 5
    assert c.zone == "Quiet"


def test_capacity_invalid_negative():
    with pytest.raises(ValueError, match="Capacity seats cannot be negative"):
        Capacity(seats=-1)


def test_capacity_invalid_zero():
    with pytest.raises(ValueError, match="Capacity seats must be at least 1"):
        Capacity(seats=0)