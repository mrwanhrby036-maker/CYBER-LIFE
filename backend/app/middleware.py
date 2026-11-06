"""Request correlation, security headers, body limits and in-process rate limiting.

The limiter is per-process and suitable for a single backend instance or tests.
Multi-instance production must add a shared limiter (API gateway/Redis) as noted
in docs/SECURITY.md; this is not represented as a distributed guarantee.
"""
import time
import uuid
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from app.logging_setup import request_id_var, get_logger
from app.errors import AppError

logger = get_logger("cyberlife.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("X-Request-ID", "")[:64] or uuid.uuid4().hex
        token = request_id_var.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
        if request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        logger.info("request", extra={"event": "http_request", "fields": {
            "method": request.method, "path": request.url.path,
            "status": response.status_code, "duration_ms": round((time.perf_counter() - start) * 1000, 2)}})
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request, call_next):
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > self.max_bytes:
            return JSONResponse(status_code=413, content={"error": {"code": "payload_too_large", "message": "حجم الطلب أكبر من الحد المسموح"}})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int, auth_per_minute: int):
        super().__init__(app)
        self.per_minute = per_minute
        self.auth_per_minute = auth_per_minute
        self.hits = defaultdict(deque)

    def _client(self, request) -> str:
        # Do not trust X-Forwarded-For unless a trusted proxy normalizes it.
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request, call_next):
        if not request.url.path.startswith("/api/") or request.url.path == "/api/health":
            return await call_next(request)
        now = time.monotonic()
        key = (self._client(request), "auth" if request.url.path.startswith("/api/auth/") else "api")
        limit = self.auth_per_minute if key[1] == "auth" else self.per_minute
        window = self.hits[key]
        while window and window[0] <= now - 60:
            window.popleft()
        if len(window) >= limit:
            return JSONResponse(status_code=429, headers={"Retry-After": "60"}, content={
                "error": {"code": "rate_limited", "message": "تجاوزت حد الطلبات؛ انتظر دقيقة"}})
        window.append(now)
        return await call_next(request)
