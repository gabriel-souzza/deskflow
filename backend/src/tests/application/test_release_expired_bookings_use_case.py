from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.release_expired import ReleaseExpiredBookingsUseCase
from domain.entities.booking import Booking, BookingStatus
from domain.value_objects.time_slot import TimeSlot


class FakeBookingRepository:
    def __init__(self, bookings):
        self.bookings = bookings
        self.saved = []
        self.deleted = []
        self.cutoffs = None

    async def find_pending_expired(self, station_cutoff, meeting_room_cutoff):
        self.cutoffs = station_cutoff, meeting_room_cutoff
        return self.bookings

    async def save(self, booking):
        self.saved.append(booking)
        return booking

    async def delete_by_booking(self, booking_id):
        self.deleted.append(booking_id)


@pytest.mark.asyncio
async def test_release_expired_bookings_expires_and_frees_bookings():
    booking = Booking(
        workspace_id=uuid4(),
        employee_id=uuid4(),
        cost_center_id=uuid4(),
        slot=TimeSlot(
            start=datetime(2020, 1, 1, 9, 0, tzinfo=UTC),
            end=datetime(2020, 1, 1, 9, 15, tzinfo=UTC),
        ),
    )
    repository = FakeBookingRepository([booking])

    released = await ReleaseExpiredBookingsUseCase(repository).execute()

    assert [item.status for item in released] == [BookingStatus.EXPIRED]
    assert repository.saved == released
    assert repository.deleted == [booking.id]
    assert repository.cutoffs[0] - repository.cutoffs[1] == timedelta(minutes=5)
