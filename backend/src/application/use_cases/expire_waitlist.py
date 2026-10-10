from datetime import UTC, datetime, timedelta

from application.use_cases.notify_waitlist import EventPublisher, NotifyWaitlistUseCase
from domain.repositories.booking_repository import BookingRepository
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.waitlist_repository import WaitlistRepository
from domain.repositories.workspace_repository import WorkspaceRepository
from domain.value_objects.time_slot import TimeSlot


class ExpireWaitlistUseCase:
    """UC05: Expira chamadas da fila de espera que ultrapassaram 5 minutos sem reserva e chama o próximo."""

    def __init__(
        self,
        waitlist_repo: WaitlistRepository,
        booking_repo: BookingRepository,
        workspace_repo: WorkspaceRepository,
        publisher: EventPublisher,
        unit_of_work: UnitOfWork,
    ):
        self.waitlist_repo = waitlist_repo
        self.booking_repo = booking_repo
        self.workspace_repo = workspace_repo
        self.notify_use_case = NotifyWaitlistUseCase(waitlist_repo, publisher, unit_of_work)
        self.unit_of_work = unit_of_work

    async def execute(self) -> int:
        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=5)
        expired_count = 0

        async with self.unit_of_work.transaction():
            active_workspaces = await self.workspace_repo.list_all_active()
            for ws in active_workspaces:
                entries = await self.waitlist_repo.list_all_by_workspace(ws.id)
                for entry in entries:
                    if (
                        entry.notified_at is not None
                        and entry.notified_at <= cutoff
                    ):
                        slot = TimeSlot(start=entry.desired_slot_start, end=entry.desired_slot_end)
                        day_key = slot.start.date().isoformat()
                        slot_index = (slot.start.hour * 60 + slot.start.minute - 8 * 60) // 15
                        occupied = await self.booking_repo.count_by_window(ws.id, day_key, slot_index)
                        if occupied < ws.capacity:
                            # Vaga ainda desocupada: notifica o próximo da fila
                            await self.notify_use_case.execute(ws.id, slot)
                            expired_count += 1

        return expired_count
