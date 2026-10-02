from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

@router.get("/utilization")
async def utilization():
    """GET /api/v1/reports/utilization — Dashboard (UC13)."""
    raise HTTPException(status_code=501, detail="Not fully implemented")

@router.get("/export")
async def export():
    """GET /api/v1/reports/export — CSV/PDF (UC14)."""
    raise HTTPException(status_code=501, detail="Not fully implemented")
