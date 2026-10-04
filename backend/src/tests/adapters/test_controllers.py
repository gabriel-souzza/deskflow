import asyncio
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from infra.database import get_db
from infra.models import Base, CostCenterORM, EmployeeORM, QuotaPeriodORM, WorkspaceORM
from infra.security import create_access_token, verify_token
from main import app


@pytest.fixture
def api_client(tmp_path):
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
    with TestClient(app) as client:
        yield client, sessions
    app.dependency_overrides.pop(get_db, None)
    asyncio.run(engine.dispose())


def test_documented_business_routes_are_registered():
    paths = app.openapi()["paths"]
    expected_routes = {
        ("/api/v1/workspaces", "get"),
        ("/api/v1/workspaces/{id}/availability", "get"),
        ("/api/v1/bookings/{id}", "delete"),
        ("/api/v1/admin/workspaces", "post"),
        ("/api/v1/availability/stream", "get"),
    }

    registered_routes = {
        (path, method) for path, operations in paths.items() for method in operations
    }

    assert expected_routes <= registered_routes


def test_booking_persistence_capacity_and_cancellation(api_client, monkeypatch):
    client, sessions = api_client

    async def seed():
        async with sessions() as session:
            center = CostCenterORM(name="Engineering", monthly_quota_hours=Decimal(40))
            session.add(center)
            await session.flush()
            employee = EmployeeORM(
                name="Test Employee",
                email="employee@example.test",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            workspace = WorkspaceORM(
                code="A-101",
                floor="1",
                zone="open",
                type="estacao",
                capacity=1,
            )
            session.add_all([employee, workspace])
            await session.commit()
            return str(center.id), str(employee.id), str(workspace.id)

    cost_center_id, employee_id, workspace_id = asyncio.run(seed())
    slot_start = datetime.combine(date.today() + timedelta(days=3), time(9))
    booking_params = {
        "workspace_id": workspace_id,
        "employee_id": employee_id,
        "cost_center_id": cost_center_id,
        "slot_start": slot_start.isoformat(),
        "slot_end": (slot_start + timedelta(minutes=30)).isoformat(),
    }
    response = client.post(
        "/api/v1/bookings",
        params=booking_params,
    )
    assert response.status_code == 201
    booking_id = response.json()["id"]
    assert response.json()["qr_token"]
    admin_token = create_access_token({"sub": "admin", "role": "admin"}, expires_delta=None)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    workspaces = client.get("/api/v1/workspaces")
    assert workspaces.status_code == 200
    assert workspaces.json()["items"][0]["code"] == "A-101"

    quota_response = client.get("/api/v1/admin/quotas", headers=admin_headers)
    assert quota_response.status_code == 200
    assert quota_response.json()["items"][0]["used_hours"] == 0.5
    quota_update = client.put(
        f"/api/v1/admin/quotas/{cost_center_id}",
        json={"monthly_quota_hours": 45},
        headers=admin_headers,
    )
    assert quota_update.status_code == 200
    assert quota_update.json()["monthly_quota_hours"] == 45

    utilization = client.get(
        "/api/v1/reports/utilization",
        params={"day": slot_start.date().isoformat()},
        headers=admin_headers,
    )
    assert utilization.status_code == 200
    assert utilization.json()["bookings_confirmed"] == 0
    csv_report = client.get(
        "/api/v1/reports/export",
        params={
            "start_date": slot_start.date().isoformat(),
            "end_date": slot_start.date().isoformat(),
        },
        headers=admin_headers,
    )
    assert csv_report.status_code == 200
    assert booking_id in csv_report.text
    pdf_report = client.get(
        "/api/v1/reports/export",
        params={
            "start_date": slot_start.date().isoformat(),
            "end_date": slot_start.date().isoformat(),
            "format": "pdf",
        },
        headers=admin_headers,
    )
    assert pdf_report.status_code == 200
    assert pdf_report.content.startswith(b"%PDF")

    workspace_create = client.post(
        "/api/v1/admin/workspaces",
        json={"code": "MR-1", "floor": "2", "zone": "meeting", "type": "sala", "capacity": 8},
        headers=admin_headers,
    )
    assert workspace_create.status_code == 201
    invalid_checkin = client.post(
        f"/api/v1/bookings/{booking_id}/checkin",
        params={"qr_token": "not-a-valid-token"},
    )
    assert invalid_checkin.status_code == 401
    from importlib import import_module

    checkin_controller = import_module("adapters.controllers.checkin_controller")

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return slot_start + timedelta(minutes=1)

    monkeypatch.setattr(checkin_controller, "datetime", FrozenDateTime)
    valid_checkin = client.post(
        f"/api/v1/bookings/{booking_id}/checkin",
        params={"qr_token": response.json()["qr_token"]},
    )
    assert valid_checkin.status_code == 200
    assert valid_checkin.json()["status"] == "CONFIRMED"

    confirmed_utilization = client.get(
        "/api/v1/reports/utilization",
        params={"day": slot_start.date().isoformat()},
        headers=admin_headers,
    )
    assert confirmed_utilization.json()["bookings_confirmed"] == 1
    availability = client.get(
        f"/api/v1/workspaces/{workspace_id}/availability",
        params={"day": slot_start.date().isoformat()},
    )
    assert availability.status_code == 200
    assert availability.json()["slots"][4]["seats_available"] == 0
    assert client.post("/api/v1/bookings", params=booking_params).status_code == 409

    cancellation = client.delete(f"/api/v1/bookings/{booking_id}")
    assert cancellation.status_code == 200
    assert cancellation.json()["status"] == "CANCELLED"
    availability = client.get(
        f"/api/v1/workspaces/{workspace_id}/availability",
        params={"day": slot_start.date().isoformat()},
    )
    assert availability.json()["slots"][4]["seats_available"] == 1

    async def assert_quota_refunded():
        async with sessions() as session:
            quota = await session.get(
                QuotaPeriodORM,
                (
                    UUID(cost_center_id),
                    datetime(slot_start.year, slot_start.month, 1),
                    (datetime(slot_start.year, slot_start.month, 28) + timedelta(days=4)).replace(
                        day=1
                    )
                    - timedelta(days=1),
                ),
            )
            assert quota is not None
            assert quota.consumed_hours == Decimal("0.00")

    asyncio.run(assert_quota_refunded())


def test_admin_quotas_requires_authentication(api_client):
    client, _sessions = api_client
    response = client.get("/api/v1/admin/quotas")
    assert response.status_code == 401


def test_admin_quotas_rejects_non_admin_token(api_client):
    client, _sessions = api_client
    token = create_access_token({"sub": "employee-1", "role": "employee"}, expires_delta=None)
    response = client.get("/api/v1/admin/quotas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_jwt_round_trip():
    token = create_access_token({"sub": "employee-1", "role": "admin"}, expires_delta=None)
    payload = verify_token(token)
    assert payload["sub"] == "employee-1"
    assert payload["role"] == "admin"
