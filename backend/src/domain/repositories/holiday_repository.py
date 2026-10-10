from abc import ABC, abstractmethod
from datetime import date

from domain.entities.holiday import Holiday


class HolidayRepository(ABC):
    @abstractmethod
    async def get_by_day(self, day: date) -> Holiday | None: ...

    @abstractmethod
    async def is_blocked(self, day: date) -> bool: ...

    @abstractmethod
    async def save(self, holiday: Holiday) -> Holiday: ...
