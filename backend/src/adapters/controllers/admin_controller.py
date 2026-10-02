from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1/admin/quotas", tags=["admin"])

@router.get("")
async def list_quotas():
    """GET /api/v1/admin/quotas — Listar quotas (UC11)."""
    raise HTTPException(status_code=501, detail="Not fully implemented")

@router.put("/{id}")
async def set_quota(id: str):
    """PUT /api/v1/admin/quotas/{id} — Configurar quota (UC11)."""
    raise HTTPException(status_code=501, detail="Not fully implemented")
