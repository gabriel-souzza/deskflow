from domain.repositories.waitlist_repository import WaitlistRepository


class NotifyWaitlistUseCase:
    """UC05: Notificar Fila de Espera (FIFO)."""

    def __init__(self, waitlist_repo: WaitlistRepository):
        self.waitlist_repo = waitlist_repo

    async def execute(self, workspace_id: str) -> None:
        pass