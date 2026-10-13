from datetime import date
from uuid import uuid4

import pytest

from domain.entities.employee import Employee


def test_employee_valid_creation():
    cc_id = uuid4()
    emp = Employee(
        name="Alice Doe",
        email="alice@company.com",
        cost_center_id=cc_id,
        is_eligible_for_booking=True,
    )
    assert emp.name == "Alice Doe"
    assert emp.email == "alice@company.com"
    assert emp.cost_center_id == cc_id
    assert emp.is_eligible_for_booking is True
    assert emp.check_eligibility(date(2026, 9, 4)) is True


def test_employee_default_ineligible():
    emp = Employee(
        name="Bob Smith",
        email="bob@company.com",
        cost_center_id=uuid4(),
    )
    assert emp.is_eligible_for_booking is False
    assert emp.check_eligibility(date(2026, 9, 4)) is False


def test_employee_validation_errors():
    cc_id = uuid4()

    with pytest.raises(ValueError, match="name is required"):
        Employee(name=None, email="a@b.com", cost_center_id=cc_id)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="email is required"):
        Employee(name="Alice", email=None, cost_center_id=cc_id)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="cost_center_id is required"):
        Employee(name="Alice", email="a@b.com", cost_center_id=None)  # type: ignore[arg-type]
