from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from domain.entities.waitlist import Waitlist
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.waitlist_repository import WaitlistRepository
from domain.value_objects.time_slot import TimeSlot


class EventPublisher(Protocol):
    async def publish(self, event: dict) -> None: ...


class NotifyWaitlistUseCase:
    """UC05: Notificar Fila de Espera (FIFO)."""

    def __init__(
        self,
        waitlist_repo: WaitlistRepository,
        event_publisher: EventPublisher,
        unit_of_work: UnitOfWork,
    ):
        self.waitlist_repo = waitlist_repo
        self.event_publisher = event_publisher
        self.unit_of_work = unit_of_work

    async def execute(self, workspace_id: UUID, slot: TimeSlot) -> Waitlist | None:
        async with self.unit_of_work.transaction():
            entries = await self.waitlist_repo.list_all_by_workspace(workspace_id)
            next_entry = next(
                (
                    entry
                    for entry in entries
                    if not entry.is_notified()
                    and entry.desired_slot_start == slot.start
                    and entry.desired_slot_end == slot.end
                ),
                None,
            )
            if next_entry is None:
                return None
            notified = next_entry.mark_notified(datetime.now(UTC))
            await self.waitlist_repo.save(notified)

        expires_at = datetime.now(UTC) + timedelta(minutes=5)
        await self.event_publisher.publish(
            {
                "type": "waitlist.notified",
                "waitlist_id": str(notified.id),
                "employee_id": str(notified.employee_id),
                "workspace_id": str(notified.workspace_id),
                "slot_start": slot.start.isoformat(),
                "slot_end": slot.end.isoformat(),
                "expires_at": expires_at.isoformat(),
            }
        )
        return notified
