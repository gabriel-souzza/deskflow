from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.entities.employee import Employee


class EmployeeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, employee_id: UUID) -> Optional[Employee]:
        ...

    @abstractmethod
    async def save(self, employee: Employee) -> Employee:
        ...