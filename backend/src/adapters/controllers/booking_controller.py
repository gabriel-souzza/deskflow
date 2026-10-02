from fastapi import APIRouter, HTTPException

from application.use_cases.create_booking import CreateBookingCommand, CreateBookingUseCase

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
    from datetime import datetime
    from uuid import UUID

    from domain.value_objects.time_slot import TimeSlot

    cmd = CreateBookingCommand(
        workspace_id=UUID(workspace_id),
        employee_id=UUID(employee_id),
        cost_center_id=UUID(cost_center_id),
        slot=TimeSlot(
            start=datetime.fromisoformat(slot_start), end=datetime.fromisoformat(slot_end)
        ),
    )
    # Nota: em produção, injetar repositórios via FastAPI Dependency
    # Aqui, criamos uma instância com repositórios placeholder para demonstração
    use_case = CreateBookingUseCase(
        booking_repo=None,
        availability_repo=None,
        quota_repo=None,
    )
    result = await use_case.execute(cmd)
    if result.status_code == 409:
        raise HTTPException(status_code=409, detail=result.message)
    if result.status_code == 402:
        raise HTTPException(status_code=402, detail=result.message)
    if result.booking is None:
        raise HTTPException(status_code=500, detail="Booking was not created")
    return result.booking
