import asyncio
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from adapters.repositories.audit_log_repo_postgres import AuditLogRepositoryPostgres
from adapters.repositories.availability_window_repo_postgres import (
    AvailabilityWindowRepositoryPostgres,
)
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.employee_repo_postgres import EmployeeRepositoryPostgres
from adapters.repositories.quota_repo_postgres import QuotaRepositoryPostgres
from adapters.repositories.waitlist_repo_postgres import WaitlistRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from domain.entities.availability_window import AvailabilityWindow
from domain.entities.booking import Booking, BookingStatus
from domain.repositories.availability_window_repository import RepositoryConflictError
from domain.value_objects.capacity import Capacity
from domain.value_objects.time_slot import TimeSlot
from infra.models import CostCenterORM, EmployeeORM, WorkspaceORM
from infra.qr_generator import generate_qr_token
from infra.unit_of_work import SqlAlchemyUnitOfWork


def test_postgres_repositories_share_transaction_and_map_entities(api_client):
    _client, sessions = api_client

    async def seed():
        async with sessions() as session:
            center = CostCenterORM(name=f"Repository {uuid4()}", monthly_quota_hours=Decimal(8))
            session.add(center)
            await session.flush()
            employee = EmployeeORM(
                name="Repository Employee",
                email=f"{uuid4().hex}@example.test",
                cost_center_id=center.id,
                is_eligible_for_booking=True,
            )
            workspace = WorkspaceORM(
                code=f"R-{uuid4()}", floor="1", zone="test", type="estacao", capacity=1
            )
            session.add_all([employee, workspace])
            await session.commit()
            return center.id, employee.id, workspace.id

    center_id, employee_id, workspace_id = asyncio.run(seed())

    async def exercise_repositories():
        async with sessions() as session:
            uow = SqlAlchemyUnitOfWork(session)
            async with uow.transaction():
                workspace_repo = WorkspaceRepositoryPostgres(session)
                employee_repo = EmployeeRepositoryPostgres(session)
                quota_repo = QuotaRepositoryPostgres(session)
                booking_repo = BookingRepositoryPostgres(session)
                window_repo = AvailabilityWindowRepositoryPostgres(session)
                waitlist_repo = WaitlistRepositoryPostgres(session)
                audit_repo = AuditLogRepositoryPostgres(session)

                workspace = await workspace_repo.get_for_booking(workspace_id)
                employee = await employee_repo.get_by_id(employee_id)
                assert workspace is not None and workspace.capacity == 1
                assert employee is not None and employee.check_eligibility(datetime.now(UTC).date())
                assert await workspace_repo.get_by_id(uuid4()) is None
                assert await employee_repo.get_by_id(uuid4()) is None
                await workspace_repo.save(replace(workspace, code="R-UPDATED"))
                await employee_repo.save(replace(employee, name="Updated Employee"))
                assert await workspace_repo.list_all_active()
                assert (await workspace_repo.get_by_id(workspace_id)).code == "R-UPDATED"

                requested_day = datetime.now(UTC).date() + timedelta(days=3)
                quota = await quota_repo.get_for_period(center_id, requested_day.isoformat())
                await quota_repo.save(quota.consume(Decimal("0.25")))

                slot_start = datetime.combine(requested_day, time(9), tzinfo=UTC)
                slot = TimeSlot(slot_start, slot_start + timedelta(minutes=15))
                window = AvailabilityWindow(
                    workspace_id=workspace_id,
                    day=requested_day.isoformat(),
                    slot_index=4,
                    capacity=Capacity(seats=1),
                )
                await window_repo.save(window)
                updated_window = replace(window, version_id=2, capacity=Capacity(seats=2))
                await window_repo.save(updated_window)
                assert await window_repo.get_by_key(workspace_id, window.day, 4) == updated_window

                # Optimistic lock check (Invariant I6)
                with pytest.raises(RepositoryConflictError):
                    await window_repo.save(
                        replace(updated_window, version_id=3), expected_version=999
                    )
                await window_repo.save(
                    replace(updated_window, version_id=3), expected_version=2
                )
                assert (
                    await window_repo.get_by_key(workspace_id, window.day, 4)
                ).version_id == 3

                booking = Booking(
                    workspace_id=workspace_id,
                    employee_id=employee_id,
                    cost_center_id=center_id,
                    slot=slot,
                )
                await booking_repo.save(booking)
                assert await booking_repo.count_by_window(workspace_id, window.day, 4) == 1
                assert await window_repo.count_by_window(workspace_id, window.day, 4) == 1
                assert await booking_repo.get_by_id_for_update(booking.id) == booking
                assert await booking_repo.get_by_id(uuid4()) is None

                await audit_repo.create(
                    actor_id=employee_id,
                    action="created",
                    entity_type="booking",
                    entity_id=str(booking.id),
                    timestamp=datetime.now(UTC).replace(tzinfo=None),
                    reason="repository test",
                )
                waitlist_entry = await waitlist_repo.create(workspace_id, employee_id, slot)
                assert (
                    await waitlist_repo.get_by_workspace_employee(workspace_id, employee_id)
                    == waitlist_entry
                )
                assert await waitlist_repo.list_all_by_workspace(workspace_id) == [waitlist_entry]
                await waitlist_repo.delete(waitlist_entry.id)
                assert await waitlist_repo.list_all_by_workspace(workspace_id) == []
                assert await waitlist_repo.get_by_workspace_employee(uuid4(), uuid4()) is None
                await booking_repo.delete_by_booking(booking.id)
                assert await booking_repo.count_by_window(workspace_id, window.day, 4) == 0
                expired_start = datetime(2020, 1, 1, 9, tzinfo=UTC)
                expired_booking = Booking(
                    workspace_id=workspace_id,
                    employee_id=employee_id,
                    cost_center_id=center_id,
                    slot=TimeSlot(expired_start, expired_start + timedelta(minutes=15)),
                )
                await booking_repo.save(expired_booking)
                expired = await booking_repo.find_pending_expired(
                    datetime.now(UTC).replace(tzinfo=None),
                    datetime.now(UTC).replace(tzinfo=None),
                )
                assert [item.id for item in expired] == [expired_booking.id]
                await booking_repo.delete_by_booking(expired_booking.id)
                assert booking.status is BookingStatus.PENDING

    asyncio.run(exercise_repositories())

    qr_image = generate_qr_token("repository-test-token")
    assert qr_image.width > 0 and qr_image.height > 0
