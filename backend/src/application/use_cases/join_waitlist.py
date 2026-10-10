from uuid import UUID

from domain.entities.waitlist import Waitlist
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.employee_repository import EmployeeRepository
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.waitlist_repository import WaitlistRepository
from domain.repositories.workspace_repository import WorkspaceRepository
from domain.value_objects.time_slot import TimeSlot


class JoinWaitlistUseCase:
    """Enroll an eligible employee once for a workspace."""

    def __init__(
        self,
        waitlist_repo: WaitlistRepository,
        workspace_repo: WorkspaceRepository,
        employee_repo: EmployeeRepository,
        booking_repo: BookingRepository,
        unit_of_work: UnitOfWork,
    ):
        self.waitlist_repo = waitlist_repo
        self.workspace_repo = workspace_repo
        self.employee_repo = employee_repo
        self.booking_repo = booking_repo
        self.unit_of_work = unit_of_work

    async def execute(
        self, workspace_id: UUID, employee_id: UUID, desired_slot: TimeSlot
    ) -> Waitlist:
        async with self.unit_of_work.transaction():
            workspace = await self.workspace_repo.get_by_id(workspace_id)
            if workspace is None:
                raise ValueError("Workspace not found")
            employee = await self.employee_repo.get_by_id(employee_id)
            if employee is None:
                raise ValueError("Employee not found")
            if not employee.check_eligibility(desired_slot.start.date()):
                raise ValueError("Employee is not eligible to book")

            existing = await self.waitlist_repo.get_by_workspace_employee(workspace_id, employee_id)
            if existing is not None:
                if (
                    existing.desired_slot_start == desired_slot.start
                    and existing.desired_slot_end == desired_slot.end
                ):
                    return existing
                raise ValueError("Employee already has a waitlist entry for this workspace")

            for slot_start in desired_slot.slots():
                slot_index = (slot_start.hour * 60 + slot_start.minute - 8 * 60) // 15
                occupied = await self.booking_repo.count_by_window(
                    workspace_id, desired_slot.start.date().isoformat(), slot_index
                )
                if occupied < workspace.capacity:
                    raise ValueError("Workspace still has capacity for this slot")

            return await self.waitlist_repo.create(workspace_id, employee_id, desired_slot)
