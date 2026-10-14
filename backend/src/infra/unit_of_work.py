from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        if self.session.in_transaction():
            async with self.session.begin_nested():
                yield
            await self.session.commit()
        else:
            async with self.session.begin():
                yield
