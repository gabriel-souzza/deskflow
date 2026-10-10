import hmac
import os
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.audit_log_repo_postgres import AuditLogRepositoryPostgres
from adapters.repositories.employee_repo_postgres import EmployeeRepositoryPostgres
from application.use_cases.sync_point import SyncPointUseCase
from infra.database import get_db
from infra.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/integrations/attendance", tags=["integrations"])


class AttendanceSync(BaseModel):
    employee_id: UUID
    days_present: list[str]


@router.post("/sync")
async def sync_attendance(
    payload: AttendanceSync,
    integration_token: Annotated[str | None, Header(alias="X-Integration-Token")] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    expected_token = os.getenv("ATTENDANCE_INTEGRATION_TOKEN", "")
    if not expected_token:
        raise HTTPException(status_code=503, detail="Attendance integration is not configured")
    if integration_token is None or not hmac.compare_digest(
        integration_token.encode("utf-8"), expected_token.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid integration token")

    try:
        employee = await SyncPointUseCase(
            EmployeeRepositoryPostgres(db),
            AuditLogRepositoryPostgres(db),
            SqlAlchemyUnitOfWork(db),
        ).execute(payload.model_dump(mode="json"))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "employee_id": str(employee.id),
        "is_eligible_for_booking": employee.is_eligible_for_booking,
    }
