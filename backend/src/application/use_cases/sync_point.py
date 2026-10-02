from domain.repositories.employee_repository import EmployeeRepository


class SyncPointUseCase:
    """UC18: Sincronização com Sistema de Ponto."""

    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo

    async def execute(self, point_data: dict) -> None:
        pass