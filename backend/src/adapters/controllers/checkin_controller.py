from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1/bookings/{id}/checkin", tags=["checkin"])

@router.post("", status_code=200)
async def checkin(id: str, qr_token: str):
    """POST /api/v1/bookings/{id}/checkin — Confirmação via QR (UC06, I4)."""
    # Implementação completa depende do ConfirmBookingUseCase
    raise HTTPException(status_code=501, detail="Not fully implemented")
