from adapters.controllers.admin_controller import router as admin_router
from adapters.controllers.booking_controller import router as booking_router
from adapters.controllers.checkin_controller import router as checkin_controller
from adapters.controllers.report_controller import router as report_router

__all__ = [
    "admin_router",
    "booking_router",
    "checkin_controller",
    "report_router",
]
