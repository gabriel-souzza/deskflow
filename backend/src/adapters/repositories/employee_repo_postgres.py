from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.employee import Employee
from domain.repositories.employee_repository import EmployeeRepository
from infra.models import EmployeeORM


class EmployeeRepositoryPostgres(EmployeeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, employee_id: UUID) -> Employee | None:
        result = await self.session.execute(
            select(EmployeeORM).where(EmployeeORM.id == employee_id)
        )
        row = result.scalars().first()
        if row is None:
            return None
        return Employee(
            id=row.id,
            name=row.name,
            email=row.email,
            cost_center_id=row.cost_center_id,
            role=getattr(row, "role", "employee"),
            is_eligible_for_booking=bool(row.is_eligible_for_booking),
        )

    async def save(self, employee: Employee) -> Employee:
        row = await self.session.get(EmployeeORM, employee.id)
        if row is None:
            row = EmployeeORM(id=employee.id)
            self.session.add(row)
        row.name = employee.name
        row.email = employee.email
        row.cost_center_id = employee.cost_center_id
        row.role = employee.role
        row.is_eligible_for_booking = employee.is_eligible_for_booking
        await self.session.flush()
        return employee
