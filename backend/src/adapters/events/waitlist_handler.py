from application.use_cases.notify_waitlist import EventPublisher, NotifyWaitlistUseCase
from domain.events.events import BookingCancelled, BookingExpired
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.waitlist_repository import WaitlistRepository


class WaitlistHandler:
    """UC05: Consumes booking release events and notifies the FIFO waitlist."""

    def __init__(
        self,
        waitlist_repo: WaitlistRepository,
        publisher: EventPublisher,
        unit_of_work: UnitOfWork,
    ):
        self.use_case = NotifyWaitlistUseCase(waitlist_repo, publisher, unit_of_work)

    async def handle_booking_cancelled(self, event: BookingCancelled) -> None:
        await self.use_case.execute(event.workspace_id, event.slot)

    async def handle_booking_expired(self, event: BookingExpired) -> None:
        await self.use_case.execute(event.workspace_id, event.slot)