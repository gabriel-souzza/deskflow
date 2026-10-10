import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.auth import require_admin
from adapters.repositories.availability_window_repo_postgres import (
    AvailabilityWindowRepositoryPostgres,
)
from adapters.repositories.holiday_repo_postgres import HolidayRepositoryPostgres
from adapters.repositories.quota_repo_postgres import QuotaRepositoryPostgres
from application.use_cases.block_holidays import BlockHolidaysUseCase
from application.use_cases.set_quota import SetQuotaUseCase
from domain.entities.holiday import Holiday
from domain.entities.quota_period import QuotaExceededError
from infra.database import get_db
from infra.models import CostCenterORM, EmployeeORM, QuotaPeriodORM
from infra.security import hash_password
from infra.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class QuotaUpdate(BaseModel):
    monthly_quota_hours: Decimal = Field(ge=0)


class HolidayCreate(BaseModel):
    day: date
    description: str = Field(default="", max_length=200)


@router.post("/holidays", status_code=201)
async def block_holiday(
    payload: HolidayCreate,
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    holiday = Holiday(day=payload.day, description=payload.description.strip())
    saved = await BlockHolidaysUseCase(
        AvailabilityWindowRepositoryPostgres(db),
        HolidayRepositoryPostgres(db),
        SqlAlchemyUnitOfWork(db),
    ).execute(holiday)
    return {"day": saved.day.isoformat(), "description": saved.description, "blocked": True}


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)
    cost_center_id: UUID
    is_eligible_for_booking: bool = False

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().casefold()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Invalid email address")
        return value


@router.post("/accounts", status_code=201)
async def create_account(
    payload: AccountCreate,
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cost_center = await db.get(CostCenterORM, payload.cost_center_id)
    if cost_center is None:
        raise HTTPException(status_code=404, detail="Cost center not found")

    existing = await db.scalar(select(EmployeeORM).where(EmployeeORM.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")

    employee = EmployeeORM(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        cost_center_id=payload.cost_center_id,
        is_eligible_for_booking=payload.is_eligible_for_booking,
    )
    db.add(employee)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered") from exc
    await db.refresh(employee)
    return {
        "id": str(employee.id),
        "name": employee.name,
        "email": employee.email,
        "cost_center_id": str(employee.cost_center_id),
        "is_eligible_for_booking": employee.is_eligible_for_booking,
    }


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
    today = date.today()
    period_start_day = today.replace(day=1)
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    period_end_day = next_month - timedelta(days=1)
    try:
        quota = await SetQuotaUseCase(
            QuotaRepositoryPostgres(db), SqlAlchemyUnitOfWork(db)
        ).execute(id, payload.monthly_quota_hours, period_start_day, period_end_day)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Cost center not found") from exc
    except QuotaExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": f"{id}:{period_start_day.isoformat()}",
        "cost_center_id": str(id),
        "monthly_quota_hours": float(quota.total_hours),
        "used_hours": float(quota.consumed_hours),
        "updated": True,
    }
