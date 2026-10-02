from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.quota_period import QuotaPeriod


class QuotaRepository(ABC):
    @abstractmethod
    async def get_for_period(
        self,
        cost_center_id: UUID,
        day: str,
    ) -> QuotaPeriod:
        """Return the QuotaPeriod that contains the given day for a cost center.

        Implementations should resolve the month containing `day` and fetch
        or create the corresponding monthly quota period.
        """
        ...

    @abstractmethod
    async def save(self, quota: QuotaPeriod) -> QuotaPeriod:
        """Persist quota consumption changes atomically."""
        ...
