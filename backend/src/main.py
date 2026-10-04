from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from adapters.controllers.admin_controller import router as admin_router
from adapters.controllers.booking_controller import router as booking_router
from adapters.controllers.checkin_controller import router as checkin_router
from adapters.controllers.report_controller import router as report_router
from adapters.controllers.workspace_controller import router as workspace_router
from adapters.events.sse_publisher import sse_publisher
from infra.security import create_access_token, hash_password, verify_password, verify_token

security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return verify_token(credentials.credentials)
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


app = FastAPI(
    title="DeskFlow API",
    description="""
Workspace reservation system for hybrid work environments.

**Features:**
- Real-time availability with 15-minute slots
- QR Code check-in with 10-minute tolerance
- Quota management per cost center
- Waitlist with SSE notifications
- JWT authentication

**OpenAPI**: `/docs`
""",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(booking_router)
app.include_router(checkin_router)
app.include_router(admin_router)
app.include_router(report_router)
app.include_router(workspace_router)


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
async def login(payload: LoginRequest):
    demo_user = {
        "admin": hash_password("admin123"),
        "employee": hash_password("deskflow123"),
    }
    hashed_password = demo_user.get(payload.username)
    if hashed_password is None or not verify_password(payload.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": payload.username, "role": payload.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
