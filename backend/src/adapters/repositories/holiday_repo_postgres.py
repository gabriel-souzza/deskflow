from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.holiday import Holiday
from domain.repositories.holiday_repository import HolidayRepository
from infra.models import HolidayORM


class HolidayRepositoryPostgres(HolidayRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_day(self, day: date) -> Holiday | None:
        row = await self.session.get(HolidayORM, day)
        if row is None:
            return None
        return Holiday(day=row.day, description=row.description or "")

    async def is_blocked(self, day: date) -> bool:
        return await self.get_by_day(day) is not None

    async def save(self, holiday: Holiday) -> Holiday:
        row = await self.session.get(HolidayORM, holiday.day)
        if row is None:
            self.session.add(HolidayORM(day=holiday.day, description=holiday.description))
        else:
            row.description = holiday.description
        await self.session.flush()
        return holiday
