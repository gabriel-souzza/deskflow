from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infra.security import verify_token

security = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return verify_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


async def require_admin(user: Annotated[dict, Depends(require_auth)]) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    return user


def require_booking_owner(user: dict, employee_id: object) -> None:
    if user.get("role") != "admin" and user.get("employee_id") != str(employee_id):
        raise HTTPException(status_code=403, detail="Booking access denied")
