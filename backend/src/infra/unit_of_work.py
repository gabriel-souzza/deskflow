from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self.session.begin():
            yield
