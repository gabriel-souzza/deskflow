import pytest
from domain.entities.booking import Booking, BookingStatus
from domain.value_objects.time_slot import TimeSlot
from datetime import datetime
from uuid import uuid4
from application.use_cases.create_booking import CreateBookingUseCase, CreateBookingCommand

@pytest.mark.asyncio
async def test_create_booking_command():
    cmd = CreateBookingCommand(
        workspace_id=uuid4(),
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        slot=TimeSlot(start=datetime(2026, 9, 4, 9, 0), end=datetime(2026, 9, 4, 9, 15)),
    )
    assert cmd.workspace_id is not None