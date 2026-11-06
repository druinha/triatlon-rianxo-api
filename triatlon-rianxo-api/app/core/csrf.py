from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}


class OriginCheckMiddleware(BaseHTTPMiddleware):
    """Protección CSRF: as peticións que modifican datos teñen que vir da nosa propia web."""

    async def dispatch(self, request: Request, call_next):
        if request.method in UNSAFE:
            origin = (request.headers.get("origin") or "").rstrip("/")
            if origin not in get_settings().origins:
                return JSONResponse(status_code=403, content={"detail": "bad_origin"})
        return await call_next(request)
