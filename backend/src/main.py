from fastapi import FastAPI
from adapters.controllers.booking_controller import router as booking_router
from adapters.controllers.checkin_controller import router as checkin_router
from adapters.controllers.admin_controller import router as admin_router
from adapters.controllers.report_controller import router as report_router

app = FastAPI(title="DeskFlow Backend", version="0.1.0")

app.include_router(booking_router)
app.include_router(checkin_router)
app.include_router(admin_router)
app.include_router(report_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)