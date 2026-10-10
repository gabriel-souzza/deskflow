import asyncio
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from infra.models import BookingORM, CostCenterORM, EmployeeORM, QuotaPeriodORM, WorkspaceORM
from infra.security import create_access_token


def test_insufficient_quota_rolls_back_booking_and_quota(api_client):
    client, sessions = api_client

    async def seed():
        async with sessions() as session:
            center = CostCenterORM(name="No quota", monthly_quota_hours=Decimal(0))
            session.add(center)
            await session.flush()
            employee = EmployeeORM(
                name="Integration Employee",
                email="integration@example.test",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            workspace = WorkspaceORM(
                code="INT-1",
                floor="1",
                zone="open",
                type="estacao",
                capacity=1,
            )
            session.add_all([employee, workspace])
            await session.commit()
            return str(center.id), str(employee.id), str(workspace.id)

    cost_center_id, employee_id, workspace_id = asyncio.run(seed())
    token = create_access_token(
        {"sub": employee_id, "role": "employee", "employee_id": employee_id}
    )
    slot_start = datetime.combine(date.today() + timedelta(days=3), time(9))
    response = client.post(
        "/api/v1/bookings",
        params={
            "workspace_id": workspace_id,
            "employee_id": employee_id,
            "cost_center_id": cost_center_id,
            "slot_start": slot_start.isoformat(),
            "slot_end": (slot_start + timedelta(minutes=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 402

    async def assert_rollback():
        async with sessions() as session:
            assert (
                await session.get(
                    QuotaPeriodORM,
                    (
                        UUID(cost_center_id),
                        datetime(slot_start.year, slot_start.month, 1),
                        (
                            datetime(slot_start.year, slot_start.month, 28) + timedelta(days=4)
                        ).replace(day=1)
                        - timedelta(days=1),
                    ),
                )
                is None
            )
            assert (await session.scalars(select(BookingORM))).all() == []

    from sqlalchemy import select

    asyncio.run(assert_rollback())
