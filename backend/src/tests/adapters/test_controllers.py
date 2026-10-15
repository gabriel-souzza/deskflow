import asyncio
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from infra.models import CostCenterORM, EmployeeORM, QuotaPeriodORM, WorkspaceORM
from infra.security import create_access_token, verify_token
from main import app


def test_documented_business_routes_are_registered():
    paths = app.openapi()["paths"]
    expected_routes = {
        ("/api/v1/workspaces", "get"),
        ("/api/v1/workspaces/{id}/availability", "get"),
        ("/api/v1/bookings", "get"),
        ("/api/v1/bookings/{id}", "get"),
        ("/api/v1/bookings/{id}", "delete"),
        ("/api/v1/admin/workspaces", "post"),
        ("/api/v1/admin/holidays", "post"),
        ("/api/v1/admin/cost-centers", "get"),
        ("/api/v1/admin/cost-centers", "post"),
        ("/api/v1/admin/accounts", "get"),
        ("/api/v1/waitlist", "post"),
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
    employee_token = create_access_token(
        {"sub": employee_id, "role": "employee", "employee_id": employee_id}
    )
    employee_headers = {"Authorization": f"Bearer {employee_token}"}
    slot_start = datetime.combine(date.today() + timedelta(days=3), time(9))
    booking_params = {
        "workspace_id": workspace_id,
        "employee_id": employee_id,
        "cost_center_id": cost_center_id,
        "slot_start": slot_start.isoformat(),
        "slot_end": (slot_start + timedelta(minutes=30)).isoformat(),
    }
    anonymous_response = client.post(
        "/api/v1/bookings",
        params=booking_params,
    )
    assert anonymous_response.status_code == 401
    other_employee_params = {**booking_params, "employee_id": str(UUID(int=1))}
    forbidden_response = client.post(
        "/api/v1/bookings",
        params=other_employee_params,
        headers=employee_headers,
    )
    assert forbidden_response.status_code == 403
    response = client.post(
        "/api/v1/bookings",
        params=booking_params,
        headers=employee_headers,
    )
    assert response.status_code == 201
    booking_id = response.json()["id"]
    assert response.json()["qr_token"]
    stranger_token = create_access_token(
        {"sub": "another-employee", "role": "employee", "employee_id": "another-employee"}
    )
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}
    assert (
        client.delete(f"/api/v1/bookings/{booking_id}", headers=stranger_headers).status_code == 403
    )
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
    assert (
        client.post("/api/v1/bookings", params=booking_params, headers=employee_headers).status_code
        == 409
    )

    cancellation = client.delete(f"/api/v1/bookings/{booking_id}", headers=employee_headers)
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


def test_waitlist_enrollment_is_idempotent_and_notified_after_cancellation(api_client):
    client, sessions = api_client

    async def seed():
        async with sessions() as session:
            center = CostCenterORM(name="Waitlist Test", monthly_quota_hours=Decimal(8))
            session.add(center)
            await session.flush()
            employee = EmployeeORM(
                name="Waitlist Employee",
                email="waitlist@example.test",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            workspace = WorkspaceORM(
                code="WAITLIST-1",
                floor="1",
                zone="open",
                type="estacao",
                capacity=1,
            )
            session.add_all([employee, workspace])
            await session.commit()
            return str(center.id), str(employee.id), str(workspace.id)

    cost_center_id, employee_id, workspace_id = asyncio.run(seed())
    headers = {
        "Authorization": "Bearer "
        + create_access_token({"sub": employee_id, "role": "employee", "employee_id": employee_id})
    }
    start = datetime.combine(date.today() + timedelta(days=3), time(9))
    end = start + timedelta(minutes=30)
    booking = client.post(
        "/api/v1/bookings",
        params={
            "workspace_id": workspace_id,
            "employee_id": employee_id,
            "cost_center_id": cost_center_id,
            "slot_start": start.isoformat(),
            "slot_end": end.isoformat(),
        },
        headers=headers,
    )
    assert booking.status_code == 201

    waitlist_payload = {
        "workspace_id": workspace_id,
        "slot_start": start.isoformat(),
        "slot_end": end.isoformat(),
    }
    joined = client.post("/api/v1/waitlist", json=waitlist_payload, headers=headers)
    repeated = client.post("/api/v1/waitlist", json=waitlist_payload, headers=headers)
    assert joined.status_code == 201
    assert repeated.status_code == 201
    assert repeated.json()["id"] == joined.json()["id"]

    cancelled = client.delete(f"/api/v1/bookings/{booking.json()['id']}", headers=headers)
    assert cancelled.status_code == 200

    from infra.models import WaitlistORM

    async def assert_notification_persisted():
        async with sessions() as session:
            entry = await session.get(WaitlistORM, UUID(joined.json()["id"]))
            assert entry is not None and entry.notified_at is not None

    asyncio.run(assert_notification_persisted())


def test_admin_quotas_requires_authentication(api_client):
    client, _sessions = api_client
    response = client.get("/api/v1/admin/quotas")
    assert response.status_code == 401


def test_hardcoded_demo_credentials_are_disabled(api_client):
    client, _sessions = api_client
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 401


def test_admin_creates_persistent_account_and_user_logs_in(api_client):
    client, sessions = api_client

    async def seed_cost_center():
        async with sessions() as session:
            center = CostCenterORM(name="Account Test", monthly_quota_hours=Decimal(8))
            session.add(center)
            await session.commit()
            return str(center.id)

    cost_center_id = asyncio.run(seed_cost_center())
    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Account Test User",
        "email": "account-test@example.test",
        "password": "DeskflowStrong#2026",
        "cost_center_id": cost_center_id,
        "is_eligible_for_booking": True,
    }

    created = client.post("/api/v1/admin/accounts", json=payload, headers=admin_headers)

    assert created.status_code == 201
    account = created.json()
    assert account["email"] == payload["email"]
    assert account["is_eligible_for_booking"] is True
    assert "password_hash" not in account

    login = client.post(
        "/api/v1/auth/login",
        json={"username": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    claims = verify_token(login.json()["access_token"])
    assert claims["sub"] == account["id"]
    assert claims["role"] == "employee"

    duplicate = client.post("/api/v1/admin/accounts", json=payload, headers=admin_headers)
    assert duplicate.status_code == 409


def test_admin_quotas_rejects_non_admin_token(api_client):
    client, _sessions = api_client
    token = create_access_token({"sub": "employee-1", "role": "employee"}, expires_delta=None)
    response = client.get("/api/v1/admin/quotas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_account_receives_admin_role_and_accesses_admin_routes(api_client):
    client, sessions = api_client

    async def seed_admin():
        from infra.security import hash_password

        async with sessions() as session:
            admin_emp = EmployeeORM(
                name="Admin User",
                email="admin@deskflow.com",
                password_hash=hash_password("Admin123456!"),
                role="admin",
                is_eligible_for_booking=True,
            )
            session.add(admin_emp)
            await session.commit()
            return str(admin_emp.id)

    asyncio.run(seed_admin())

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@deskflow.com", "password": "Admin123456!"},
    )
    assert login.status_code == 200
    claims = verify_token(login.json()["access_token"])
    assert claims["role"] == "admin"

    auth_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    quotas_response = client.get("/api/v1/admin/quotas", headers=auth_headers)
    assert quotas_response.status_code == 200


def test_jwt_round_trip():
    token = create_access_token({"sub": "employee-1", "role": "admin"}, expires_delta=None)
    payload = verify_token(token)
    assert payload["sub"] == "employee-1"
    assert payload["role"] == "admin"
    assert payload["exp"] > datetime.now(UTC).timestamp()


def test_list_and_get_bookings_endpoint(api_client):
    client, sessions = api_client

    async def seed():
        async with sessions() as session:
            center = CostCenterORM(name="List Booking CC", monthly_quota_hours=Decimal(40))
            session.add(center)
            await session.flush()
            emp1 = EmployeeORM(
                name="Emp One",
                email="emp1@test.com",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            emp2 = EmployeeORM(
                name="Emp Two",
                email="emp2@test.com",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            ws = WorkspaceORM(code="WS-LIST", floor="1", zone="open", type="estacao", capacity=1)
            session.add_all([emp1, emp2, ws])
            await session.commit()
            return str(center.id), str(emp1.id), str(emp2.id), str(ws.id)

    cc_id, emp1_id, emp2_id, ws_id = asyncio.run(seed())
    t1 = create_access_token({"sub": emp1_id, "role": "employee", "employee_id": emp1_id})
    t2 = create_access_token({"sub": emp2_id, "role": "employee", "employee_id": emp2_id})
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    # Emp1 creates a booking
    slot_start = datetime.combine(date.today() + timedelta(days=2), time(10))
    res = client.post(
        "/api/v1/bookings",
        json={
            "workspace_id": ws_id,
            "employee_id": emp1_id,
            "cost_center_id": cc_id,
            "slot_start": slot_start.isoformat(),
            "slot_end": (slot_start + timedelta(minutes=30)).isoformat(),
        },
        headers=h1,
    )
    assert res.status_code == 201
    booking_id = res.json()["id"]

    # Emp1 lists own bookings
    list_res = client.get("/api/v1/bookings", headers=h1)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(b["id"] == booking_id for b in items)

    # Emp1 gets single booking
    get_res = client.get(f"/api/v1/bookings/{booking_id}", headers=h1)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == booking_id
    assert get_res.json()["status"] == "PENDING"

    # Emp2 cannot access Emp1's booking
    forbidden_res = client.get(f"/api/v1/bookings/{booking_id}", headers=h2)
    assert forbidden_res.status_code == 403

    # Nonexistent booking 404
    from uuid import uuid4

    not_found = client.get(f"/api/v1/bookings/{uuid4()}", headers=h1)
    assert not_found.status_code == 404


def test_admin_cost_centers_and_accounts_endpoints(api_client):
    client, sessions = api_client

    async def seed():
        from infra.security import hash_password

        async with sessions() as session:
            admin = EmployeeORM(
                name="Admin Super",
                email="admin.super@deskflow.com",
                password_hash=hash_password("Admin123456!"),
                role="admin",
                is_eligible_for_booking=True,
            )
            session.add(admin)
            await session.commit()
            return str(admin.id)

    admin_id = asyncio.run(seed())
    admin_token = create_access_token({"sub": admin_id, "role": "admin"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_token = create_access_token({"sub": "user-1", "role": "employee", "employee_id": "user-1"})
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Employee cannot access admin cost-centers or accounts
    assert client.get("/api/v1/admin/cost-centers", headers=user_headers).status_code == 403
    assert client.get("/api/v1/admin/accounts", headers=user_headers).status_code == 403

    # Admin creates cost center
    create_cc = client.post(
        "/api/v1/admin/cost-centers",
        json={"name": "Logistics & Supply", "monthly_quota_hours": 120.0},
        headers=admin_headers,
    )
    assert create_cc.status_code == 201
    cc_data = create_cc.json()
    assert cc_data["name"] == "Logistics & Supply"
    assert cc_data["monthly_quota_hours"] == 120.0

    # Duplicate cost center name rejected with 409
    dup_cc = client.post(
        "/api/v1/admin/cost-centers",
        json={"name": "Logistics & Supply", "monthly_quota_hours": 120.0},
        headers=admin_headers,
    )
    assert dup_cc.status_code == 409

    # Admin lists cost centers
    list_cc = client.get("/api/v1/admin/cost-centers", headers=admin_headers)
    assert list_cc.status_code == 200
    names = [c["name"] for c in list_cc.json()["items"]]
    assert "Logistics & Supply" in names

    # Admin lists accounts
    list_acc = client.get("/api/v1/admin/accounts", headers=admin_headers)
    assert list_acc.status_code == 200
    accounts = list_acc.json()["items"]
    assert any(acc["email"] == "admin.super@deskflow.com" for acc in accounts)
