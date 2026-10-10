from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from domain.entities.employee import Employee
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.repositories.employee_repository import EmployeeRepository
from domain.repositories.unit_of_work import UnitOfWork


class SyncPointUseCase:
    """UC18: Sincronização com Sistema de Ponto."""

    def __init__(
        self,
        employee_repo: EmployeeRepository,
        audit_log_repo: AuditLogRepository,
        unit_of_work: UnitOfWork,
    ):
        self.employee_repo = employee_repo
        self.audit_log_repo = audit_log_repo
        self.unit_of_work = unit_of_work

    async def execute(self, point_data: dict[str, Any]) -> Employee:
        try:
            employee_id = UUID(str(point_data["employee_id"]))
            days_present = {date.fromisoformat(str(day)) for day in point_data["days_present"]}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("employee_id and ISO days_present are required") from exc

        async with self.unit_of_work.transaction():
            employee = await self.employee_repo.get_by_id(employee_id)
            if employee is None:
                raise LookupError("Employee not found")
            updated = replace(employee, is_eligible_for_booking=len(days_present) >= 3)
            await self.employee_repo.save(updated)
            await self.audit_log_repo.create(
                actor_id=employee.id,
                action="attendance_synced",
                entity_type="employee",
                entity_id=str(employee.id),
                timestamp=datetime.now(UTC).replace(tzinfo=None),
                reason=f"{len(days_present)} distinct attendance days",
            )
            return updated
