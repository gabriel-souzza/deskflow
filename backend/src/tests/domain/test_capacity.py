from domain.value_objects.capacity import Capacity

def test_capacity_valid():
    c = Capacity(seats=5)
    assert c.seats == 5

def test_capacity_invalid_negative():
    try:
        Capacity(seats=-1)
        assert False
    except ValueError:
        pass