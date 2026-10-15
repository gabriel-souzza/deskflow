import re
from datetime import date, datetime, timedelta
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
    role: str = Field(default="employee", pattern=r"^(employee|admin)$")
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
        role=payload.role,
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
        "role": employee.role,
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


class CostCenterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    monthly_quota_hours: Decimal = Field(default=Decimal(0), ge=0)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Cost center name cannot be blank")
        return value


@router.get("/cost-centers")
async def list_cost_centers(
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/admin/cost-centers — Listar centros de custo."""
    result = await db.execute(select(CostCenterORM).order_by(CostCenterORM.name))
    centers = result.scalars().all()
    return {
        "items": [
            {
                "id": str(center.id),
                "name": center.name,
                "monthly_quota_hours": float(center.monthly_quota_hours),
            }
            for center in centers
        ]
    }


@router.post("/cost-centers", status_code=201)
async def create_cost_center(
    payload: CostCenterCreate,
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/admin/cost-centers — Criar novo centro de custo."""
    existing = await db.scalar(select(CostCenterORM).where(CostCenterORM.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Cost center name already exists")

    center = CostCenterORM(
        name=payload.name,
        monthly_quota_hours=payload.monthly_quota_hours,
    )
    db.add(center)
    await db.flush()

    today = date.today()
    period_start = datetime.combine(today.replace(day=1), datetime.min.time())
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    period_end = datetime.combine(next_month, datetime.min.time())

    quota_period = QuotaPeriodORM(
        cost_center_id=center.id,
        period_start=period_start,
        period_end=period_end,
        total_hours=payload.monthly_quota_hours,
        consumed_hours=Decimal(0),
    )
    db.add(quota_period)
    await db.commit()
    await db.refresh(center)

    return {
        "id": str(center.id),
        "name": center.name,
        "monthly_quota_hours": float(center.monthly_quota_hours),
    }


@router.get("/accounts")
async def list_accounts(
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/admin/accounts — Listar colaboradores cadastrados."""
    result = await db.execute(
        select(EmployeeORM, CostCenterORM)
        .outerjoin(CostCenterORM, CostCenterORM.id == EmployeeORM.cost_center_id)
        .order_by(EmployeeORM.name)
    )
    return {
        "items": [
            {
                "id": str(emp.id),
                "name": emp.name,
                "email": emp.email,
                "role": emp.role,
                "cost_center_id": str(emp.cost_center_id) if emp.cost_center_id else None,
                "cost_center_name": center.name if center else None,
                "is_eligible_for_booking": emp.is_eligible_for_booking,
            }
            for emp, center in result.all()
        ]
    }
