import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "deskflow-test-jwt-secret-with-at-least-32-bytes"
os.environ["DEMO_ADMIN_USERNAME"] = ""
os.environ["DEMO_ADMIN_PASSWORD"] = ""


@pytest.fixture
def api_client(tmp_path):
    from infra.database import get_db
    from infra.models import Base
    from main import app

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'deskflow-test.sqlite'}",
        poolclass=NullPool,
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def create_schema():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(create_schema())

    async def override_get_db():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, sessions
    finally:
        app.dependency_overrides.pop(get_db, None)
        asyncio.run(engine.dispose())
