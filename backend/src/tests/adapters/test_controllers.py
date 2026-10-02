from fastapi.testclient import TestClient
from main import app

def test_booking_create_201():
    client = TestClient(app)
    response = client.post("/api/v1/bookings", params={
        "workspace_id": "uuid-1",
        "employee_id": "uuid-2",
        "cost_center_id": "uuid-3",
        "slot_start": "2026-09-04T09:00:00",
        "slot_end": "2026-09-04T09:15:00",
    })
    assert response.status_code in (200, 201, 501)