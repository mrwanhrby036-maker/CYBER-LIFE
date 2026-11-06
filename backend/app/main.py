"""CYBER LIFE FastAPI application factory."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import Settings, get_settings
from app.middleware import RequestContextMiddleware, BodySizeLimitMiddleware, RateLimitMiddleware
from app.db_local import LocalRepository
from app.db_firebase import FirebaseRepository
from app.tokens import LocalTokenService, FirebaseAuthService
from app.service_content import ContentService
from app.service_users import UserService
from app.errors import AppError
from app.logging_setup import configure_logging, get_logger, request_id_var
from app import route_health
from app import route_auth
from app import route_curriculum
from app import route_progress
from app import route_teams
from app import route_missions
from app import route_laboratory
from app import route_reports
from app import route_achievements
from app import route_admin

logger = get_logger("cyberlife")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.storage_mode == "local":
            repo = LocalRepository(settings.resolve(settings.data_dir), fsync=settings.local_fsync)
        else:
            repo = FirebaseRepository(settings)
        app.state.repository = repo
        app.state.settings = settings
        app.state.local_tokens = LocalTokenService(settings) if settings.auth_mode == "local" else None
        app.state.firebase_auth = FirebaseAuthService(repo) if settings.auth_mode == "firebase" else None
        app.state.content = ContentService(repo, settings.resolve(settings.content_dir))
        users = UserService(repo, settings, app.state.local_tokens)
        await users.initialize_local_accounts()
        if not await repo.get("platform_settings/schema_version"):
            counts = await app.state.content.seed()
            logger.info("content_seeded", extra={"event": "content_seeded", "fields": counts})
        logger.info("startup", extra={"event": "startup", "fields": {
            "env": settings.env, "auth": settings.auth_mode, "storage": settings.storage_mode}})
        try:
            yield
        finally:
            await repo.close()

    app = FastAPI(title="CYBER LIFE API", version="1.0.0", lifespan=lifespan,
                  docs_url="/api/docs" if settings.env == "development" else None,
                  redoc_url=None, openapi_url="/api/openapi.json" if settings.env == "development" else None)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute,
                       auth_per_minute=settings.auth_rate_limit_per_minute)
    if settings.origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.origins,
                           allow_origin_regex=settings.cors_origin_regex or None,
                           allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                           allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
                           expose_headers=["X-Request-ID"], max_age=600)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"error": {
            "code": exc.code, "message": exc.message, "details": exc.details,
            "request_id": request_id_var.get()}})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(x) for x in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content={"error": {
            "code": "validation_error", "message": "تحقق من الحقول المرسلة", "details": details,
            "request_id": request_id_var.get()}})

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("unhandled_error", extra={"event": "unhandled_error", "fields": {"path": request.url.path}})
        return JSONResponse(status_code=500, content={"error": {
            "code": "internal_error", "message": "حدث خطأ داخلي؛ حاول لاحقاً", "request_id": request_id_var.get()}})

    for module in (route_health, route_auth, route_curriculum, route_progress, route_teams, route_missions, route_laboratory, route_reports, route_achievements, route_admin):
        app.include_router(module.router, prefix="/api")

    if settings.serve_frontend:
        frontend = settings.resolve(settings.frontend_dir)
        if frontend.exists():
            app.mount("/", StaticFiles(directory=str(frontend), html=True), name="frontend")
    return app


app = create_app()
