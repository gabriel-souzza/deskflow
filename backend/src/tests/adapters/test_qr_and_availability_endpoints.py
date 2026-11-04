import asyncio
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from infra.models import CostCenterORM, EmployeeORM, WorkspaceORM
from infra.security import create_access_token


def test_qr_and_json_body_endpoints(api_client):
    client, sessions = api_client

    async def seed():
        async with sessions() as session:
            center = CostCenterORM(name="Tech", monthly_quota_hours=Decimal(40))
            session.add(center)
            await session.flush()
            employee = EmployeeORM(
                name="QR Tester",
                email="qr_tester@example.test",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            workspace = WorkspaceORM(
                code="QR-101",
                floor="2",
                zone="quiet",
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
    headers = {"Authorization": f"Bearer {employee_token}"}
    slot_start = datetime.combine(datetime.now(UTC).date() + timedelta(days=2), time(10))
    slot_end = slot_start + timedelta(minutes=30)

    # 1. Test POST /api/v1/bookings with JSON Body
    booking_payload = {
        "workspace_id": workspace_id,
        "employee_id": employee_id,
        "cost_center_id": cost_center_id,
        "slot_start": slot_start.isoformat(),
        "slot_end": slot_end.isoformat(),
    }
    create_res = client.post("/api/v1/bookings", json=booking_payload, headers=headers)
    assert create_res.status_code == 201
    booking_data = create_res.json()
    booking_id = booking_data["id"]
    assert "qr_token" in booking_data

    # 2. Test GET /api/v1/bookings/{id}/qr returns image/png with auth header
    assert client.get(f"/api/v1/bookings/{booking_id}/qr").status_code == 401
    qr_res = client.get(f"/api/v1/bookings/{booking_id}/qr", headers=headers)
    assert qr_res.status_code == 200
    assert qr_res.headers["content-type"] == "image/png"
    assert "X-Checkin-Token" in qr_res.headers
    assert len(qr_res.content) > 100

    # Test GET /api/v1/bookings/{id}/qr with query param token
    qr_query_res = client.get(f"/api/v1/bookings/{booking_id}/qr?token={employee_token}")
    assert qr_query_res.status_code == 200
    assert qr_query_res.headers["content-type"] == "image/png"
    assert len(qr_query_res.content) > 100

    # Test GET /api/v1/bookings/{id}/checkin-token
    token_res = client.get(f"/api/v1/bookings/{booking_id}/checkin-token", headers=headers)
    assert token_res.status_code == 200
    assert "qr_token" in token_res.json()

    # Test QR 404 for unknown booking
    assert client.get(f"/api/v1/bookings/{UUID(int=999)}/qr", headers=headers).status_code == 404

    # 3. Test GET /api/v1/availability with filters
    avail_res = client.get(
        "/api/v1/availability",
        params={"day": slot_start.date().isoformat(), "floor": "2"},
        headers=headers,
    )
    assert avail_res.status_code == 200
    workspaces = avail_res.json()["workspaces"]
    assert any(w["code"] == "QR-101" for w in workspaces)

    # 4. Test POST /api/v1/bookings/{id}/checkin with JSON body
    # Using a fake non-matching token gives 401
    checkin_fake = client.post(
        f"/api/v1/bookings/{booking_id}/checkin",
        json={"qr_token": "invalid-token"},
    )
    assert checkin_fake.status_code == 401

    # 5. Test Health and Metrics endpoints
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    assert "deskflow_up 1" in metrics_res.text
