from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database import get_db
from infra.models import CostCenterORM, QuotaPeriodORM
from infra.security import verify_token

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
security = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return verify_token(credentials.credentials)
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


async def require_admin(user=Depends(require_auth)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    return user


class QuotaUpdate(BaseModel):
    monthly_quota_hours: Decimal = Field(ge=0)


@router.get("/quotas")
async def list_quotas(_user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """GET /api/v1/admin/quotas — Listar quotas (UC11)."""
    result = await db.execute(
        select(QuotaPeriodORM, CostCenterORM)
        .join(CostCenterORM, CostCenterORM.id == QuotaPeriodORM.cost_center_id)
        .order_by(QuotaPeriodORM.period_start.desc(), CostCenterORM.name)
    )
    return {
        "items": [
            {
                "id": f"{quota.cost_center_id}:{quota.period_start.date().isoformat()}",
                "cost_center_id": str(center.id),
                "cost_center_name": center.name,
                "period_start": quota.period_start.date().isoformat(),
                "period_end": quota.period_end.date().isoformat(),
                "monthly_quota_hours": float(quota.total_hours),
                "used_hours": float(quota.consumed_hours),
            }
            for quota, center in result.all()
        ]
    }


@router.put("/quotas/{id}")
async def set_quota(
    id: UUID,
    payload: QuotaUpdate,
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """PUT /api/v1/admin/quotas/{id} — Configurar quota (UC11)."""
    cost_center = await db.get(CostCenterORM, id)
    if cost_center is None:
        raise HTTPException(status_code=404, detail="Cost center not found")
    today = date.today()
    period_start = datetime.combine(today.replace(day=1), time.min)
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    period_end = datetime.combine(next_month - timedelta(days=1), time.min)
    quota = await db.scalar(
        select(QuotaPeriodORM).where(
            QuotaPeriodORM.cost_center_id == id,
            QuotaPeriodORM.period_start == period_start,
        )
    )
    if quota is not None and payload.monthly_quota_hours < quota.consumed_hours:
        raise HTTPException(
            status_code=409, detail="Quota cannot be set below hours already consumed"
        )
    if quota is None:
        quota = QuotaPeriodORM(
            cost_center_id=id,
            period_start=period_start,
            period_end=period_end,
            total_hours=payload.monthly_quota_hours,
            consumed_hours=Decimal(0),
        )
        db.add(quota)
    else:
        quota.total_hours = payload.monthly_quota_hours
        quota.period_end = period_end
    cost_center.monthly_quota_hours = payload.monthly_quota_hours
    await db.commit()
    return {
        "id": f"{id}:{period_start.date().isoformat()}",
        "cost_center_id": str(id),
        "monthly_quota_hours": float(quota.total_hours),
        "used_hours": float(quota.consumed_hours),
        "updated": True,
    }
