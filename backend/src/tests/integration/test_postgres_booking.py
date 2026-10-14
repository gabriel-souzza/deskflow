import asyncio
import os
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from infra.database import get_db
from infra.models import (
    AuditLogORM,
    BookingORM,
    BookingWindowORM,
    CostCenterORM,
    EmployeeORM,
    QuotaPeriodORM,
    WorkspaceORM,
)
from infra.security import create_access_token
from main import app


@pytest.mark.integration
def test_postgres_migrations_booking_and_quota_refund(monkeypatch):
    from pathlib import Path

    from dotenv import load_dotenv

    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database")

    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(Config("src/infra/migrations/alembic.ini"), "head")

    engine = create_async_engine(database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def seed():
        async with sessions.begin() as session:
            center = CostCenterORM(
                name=f"Postgres test {uuid4()}",
                monthly_quota_hours=Decimal(8),
            )
            session.add(center)
            await session.flush()
            employee = EmployeeORM(
                name="Postgres Test Employee",
                email=f"{uuid4().hex}@example.test",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            workspace = WorkspaceORM(
                code=f"PG-{uuid4()}",
                floor="1",
                zone="test",
                type="estacao",
                capacity=1,
            )
            session.add_all([center, employee, workspace])
            await session.flush()
            return center.id, employee.id, workspace.id

    center_id, employee_id, workspace_id = asyncio.run(seed())
    token = create_access_token(
        {"sub": str(employee_id), "role": "employee", "employee_id": str(employee_id)}
    )

    async def override_get_db():
        async with sessions() as session:
            yield session

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    booking_id = None
    try:
        with TestClient(app) as client:
            slot_start = datetime.combine(datetime.now(UTC).date() + timedelta(days=3), time(9))
            params = {
                "workspace_id": str(workspace_id),
                "employee_id": str(employee_id),
                "cost_center_id": str(center_id),
                "slot_start": slot_start.isoformat(),
                "slot_end": (slot_start + timedelta(minutes=30)).isoformat(),
            }
            headers = {"Authorization": f"Bearer {token}"}
            created = client.post("/api/v1/bookings", params=params, headers=headers)
            assert created.status_code == 201
            booking_id = UUID(created.json()["id"])

            async def assert_created_state():
                async with sessions() as session:
                    booking = await session.get(BookingORM, booking_id)
                    assert booking is not None and booking.status == "PENDING"
                    quota = await session.scalar(
                        select(QuotaPeriodORM).where(QuotaPeriodORM.cost_center_id == center_id)
                    )
                    assert quota is not None
                    assert quota.consumed_hours == Decimal("0.50")
                    windows = await session.scalars(
                        select(BookingWindowORM).where(BookingWindowORM.booking_id == booking_id)
                    )
                    assert len(windows.all()) == 2

            asyncio.run(assert_created_state())
            cancelled = client.delete(f"/api/v1/bookings/{booking_id}", headers=headers)
            assert cancelled.status_code == 200

            async def assert_cancelled_state():
                async with sessions() as session:
                    booking = await session.get(BookingORM, booking_id)
                    assert booking is not None and booking.status == "CANCELLED"
                    quota = await session.scalar(
                        select(QuotaPeriodORM).where(QuotaPeriodORM.cost_center_id == center_id)
                    )
                    assert quota is not None and quota.consumed_hours == Decimal("0.00")
                    windows = await session.scalars(
                        select(BookingWindowORM).where(BookingWindowORM.booking_id == booking_id)
                    )
                    assert windows.all() == []

            asyncio.run(assert_cancelled_state())
    finally:
        app.dependency_overrides.pop(get_db, None)
        if previous_override is not None:
            app.dependency_overrides[get_db] = previous_override

        async def cleanup():
            async with sessions.begin() as session:
                if booking_id is not None:
                    await session.execute(
                        delete(AuditLogORM).where(AuditLogORM.entity_id == str(booking_id))
                    )
                await session.execute(
                    delete(BookingWindowORM).where(BookingWindowORM.workspace_id == workspace_id)
                )
                await session.execute(
                    delete(BookingORM).where(BookingORM.workspace_id == workspace_id)
                )
                await session.execute(
                    delete(QuotaPeriodORM).where(QuotaPeriodORM.cost_center_id == center_id)
                )
                await session.execute(delete(EmployeeORM).where(EmployeeORM.id == employee_id))
                await session.execute(delete(WorkspaceORM).where(WorkspaceORM.id == workspace_id))
                await session.execute(delete(CostCenterORM).where(CostCenterORM.id == center_id))

        asyncio.run(cleanup())
        asyncio.run(engine.dispose())
