from fastapi import APIRouter, HTTPException, status
from application.use_cases.create_booking import CreateBookingUseCase, CreateBookingCommand, CreateBookingResult
from domain.entities.booking import BookingStatus

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

@router.post("", status_code=201)
async def create_booking(
    workspace_id: str,
    employee_id: str,
    cost_center_id: str,
    slot_start: str,
    slot_end: str,
):
    """POST /api/v1/bookings — Criar reserva (UC02)."""
    from uuid import UUID
    from domain.value_objects.time_slot import TimeSlot
    from datetime import datetime

    cmd = CreateBookingCommand(
        workspace_id=UUID(workspace_id),
        employee_id=UUID(employee_id),
        cost_center_id=UUID(cost_center_id),
        slot=TimeSlot(start=datetime.fromisoformat(slot_start), end=datetime.fromisoformat(slot_end)),
    )
    result = await CreateBookingUseCase.execute(cmd)
    if result.status_code == 409:
        raise HTTPException(status_code=409, detail=result.message)
    if result.status_code == 402:
        raise HTTPException(status_code=402, detail=result.message)
    return result.booking
