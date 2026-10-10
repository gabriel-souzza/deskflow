import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.controllers.admin_controller import router as admin_router
from adapters.controllers.booking_controller import router as booking_router
from adapters.controllers.checkin_controller import router as checkin_router
from adapters.controllers.integration_controller import router as integration_router
from adapters.controllers.report_controller import router as report_router
from adapters.controllers.waitlist_controller import router as waitlist_router
from adapters.controllers.workspace_controller import router as workspace_router
from adapters.events.in_memory_event_bus import event_bus
from adapters.events.quota_alert_handler import QuotaAlertHandler
from adapters.events.sse_publisher import sse_publisher
from adapters.repositories.availability_window_repo_postgres import (
    AvailabilityWindowRepositoryPostgres,
)
from adapters.repositories.booking_repo_postgres import BookingRepositoryPostgres
from adapters.repositories.holiday_repo_postgres import HolidayRepositoryPostgres
from adapters.repositories.waitlist_repo_postgres import WaitlistRepositoryPostgres
from adapters.repositories.workspace_repo_postgres import WorkspaceRepositoryPostgres
from application.use_cases.expire_waitlist import ExpireWaitlistUseCase
from application.use_cases.generate_daily_availability import GenerateDailyAvailabilityUseCase
from application.use_cases.notify_waitlist import NotifyWaitlistUseCase
from application.use_cases.release_expired import ReleaseExpiredBookingsUseCase
from domain.events.events import QuotaConsumed
from infra.database import SessionLocal, get_db
from infra.models import EmployeeORM
from infra.security import create_access_token, verify_password
from infra.unit_of_work import SqlAlchemyUnitOfWork

# Register global domain event handlers
quota_alert_handler = QuotaAlertHandler(sse_publisher)
event_bus.subscribe(QuotaConsumed, quota_alert_handler.handle_quota_consumed)


async def release_expired_bookings_job() -> None:
    async with SessionLocal() as session:
        uow = SqlAlchemyUnitOfWork(session)
        booking_repo = BookingRepositoryPostgres(session)
        waitlist_repo = WaitlistRepositoryPostgres(session)
        ws_repo = WorkspaceRepositoryPostgres(session)

        # Release bookings past tolerance
        released = await ReleaseExpiredBookingsUseCase(
            booking_repo=booking_repo,
            unit_of_work=uow,
            event_bus=event_bus,
        ).execute()

        for booking in released:
            await NotifyWaitlistUseCase(
                waitlist_repo,
                sse_publisher,
                uow,
            ).execute(booking.workspace_id, booking.slot)

        # Expire 5-minute waitlist notifications where slot was not booked
        expire_waitlist_use_case = ExpireWaitlistUseCase(
            waitlist_repo=waitlist_repo,
            booking_repo=booking_repo,
            workspace_repo=ws_repo,
            publisher=sse_publisher,
            unit_of_work=uow,
        )
        await expire_waitlist_use_case.execute()


async def generate_daily_availability_job() -> None:
    async with SessionLocal() as session:
        use_case = GenerateDailyAvailabilityUseCase(
            AvailabilityWindowRepositoryPostgres(session),
            WorkspaceRepositoryPostgres(session),
            HolidayRepositoryPostgres(session),
            SqlAlchemyUnitOfWork(session),
        )
        await use_case.execute(date.today().isoformat())


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        release_expired_bookings_job,
        "interval",
        minutes=1,
        id="release-expired-bookings",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        generate_daily_availability_job,
        "cron",
        hour=0,
        minute=5,
        id="generate-daily-availability",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


class LoginRequest(BaseModel):
    username: str
    password: str


app = FastAPI(
    title="DeskFlow API",
    description="""
Workspace reservation system for hybrid work environments.

**Features:**
- Real-time availability with 15-minute slots
- QR Code check-in with 10-minute tolerance
- Quota management per cost center with 80%/95% alerts
- Waitlist with SSE notifications
- JWT authentication

**OpenAPI**: `/docs`
""",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.include_router(booking_router)
app.include_router(checkin_router)
app.include_router(admin_router)
app.include_router(report_router)
app.include_router(workspace_router)
app.include_router(waitlist_router)
app.include_router(integration_router)


@app.get("/api/v1/availability/stream", tags=["availability"])
async def availability_stream():
    async def events():
        async for event in sse_publisher.subscribe():
            if event:
                yield f"data: {event}\n\n"
            else:
                yield ": heartbeat\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/api/v1/auth/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    demo_admin_username = os.getenv("DEMO_ADMIN_USERNAME", "")
    demo_admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "")
    if (
        demo_admin_username
        and demo_admin_password
        and secrets.compare_digest(
            payload.username.encode("utf-8"), demo_admin_username.encode("utf-8")
        )
        and secrets.compare_digest(
            payload.password.encode("utf-8"), demo_admin_password.encode("utf-8")
        )
    ):
        token = create_access_token({"sub": demo_admin_username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}

    email = payload.username.strip().casefold()
    employee = await db.scalar(select(EmployeeORM).where(EmployeeORM.email == email))
    if employee is None or not employee.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, employee.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {"sub": str(employee.id), "role": "employee", "employee_id": str(employee.id)}
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:  # noqa: BLE001
        db_status = "degraded"
    return {"status": "ok", "database": db_status}


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible health metrics format (RNF01/RNF02)."""
    lines = [
        "# HELP deskflow_up System availability status (1 = up)",
        "# TYPE deskflow_up gauge",
        "deskflow_up 1",
    ]
    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
