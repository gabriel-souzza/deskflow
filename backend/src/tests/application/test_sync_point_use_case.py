from contextlib import asynccontextmanager
from datetime import date
from uuid import uuid4

import pytest

from application.use_cases.sync_point import SyncPointUseCase
from domain.entities.employee import Employee


class FakeUnitOfWork:
    @asynccontextmanager
    async def transaction(self):
        yield


class FakeEmployeeRepository:
    def __init__(self, employee):
        self.employee = employee
        self.saved = []

    async def get_by_id(self, employee_id):
        return self.employee if self.employee and self.employee.id == employee_id else None

    async def save(self, employee):
        self.employee = employee
        self.saved.append(employee)
        return employee


class FakeAuditRepository:
    def __init__(self):
        self.entries = []

    async def create(self, **entry):
        self.entries.append(entry)


@pytest.mark.asyncio
async def test_sync_point_eligibility_requires_three_distinct_presence_days():
    employee = Employee(
        id=uuid4(),
        name="Employee",
        email="employee@example.test",
        cost_center_id=uuid4(),
        is_eligible_for_booking=False,
    )
    repo = FakeEmployeeRepository(employee)
    audit = FakeAuditRepository()
    use_case = SyncPointUseCase(repo, audit, FakeUnitOfWork())

    updated = await use_case.execute(
        {
            "employee_id": str(employee.id),
            "days_present": ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-07"],
        }
    )

    assert updated.is_eligible_for_booking is True
    assert repo.saved == [updated]
    assert audit.entries[0]["action"] == "attendance_synced"


@pytest.mark.asyncio
async def test_sync_point_disables_eligibility_below_three_days():
    employee = Employee(
        id=uuid4(),
        name="Employee",
        email="employee@example.test",
        cost_center_id=uuid4(),
        is_eligible_for_booking=True,
    )
    use_case = SyncPointUseCase(
        FakeEmployeeRepository(employee), FakeAuditRepository(), FakeUnitOfWork()
    )

    updated = await use_case.execute(
        {"employee_id": str(employee.id), "days_present": [date(2026, 10, 5).isoformat()]}
    )

    assert updated.is_eligible_for_booking is False


@pytest.mark.asyncio
async def test_sync_point_rejects_bad_data_and_missing_employee():
    use_case = SyncPointUseCase(
        FakeEmployeeRepository(None), FakeAuditRepository(), FakeUnitOfWork()
    )

    with pytest.raises(ValueError, match="employee_id"):
        await use_case.execute({"days_present": []})
    with pytest.raises(LookupError, match="Employee not found"):
        await use_case.execute({"employee_id": str(uuid4()), "days_present": []})
