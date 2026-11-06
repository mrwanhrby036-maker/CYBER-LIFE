from fastapi import APIRouter, Request
from app.helpers import utc_now

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request):
    settings = request.app.state.settings
    return {"status": "ok", "service": "CYBER LIFE", "time": utc_now(), "version": "1.0.0"}


@router.get("/health/ready")
async def ready(request: Request):
    content = await request.app.state.repository.get("platform_settings/schema_version")
    return {"status": "ok" if content else "degraded", "content_seeded": bool(content)}
