from fastapi import APIRouter, Depends, Query, Request
from pydantic import Field
from app.dependencies import admin_principal, Principal
from app.schemas import StrictModel, RoleUpdate, ContentPublish, AdminContent
from app.service_users import UserService
from app.service_content import ContentService, COLLECTIONS
from app.service_analytics import AnalyticsService
from app.service_reports import ReportService
from app.service_audit import AuditService
from app.logging_setup import request_id_var

router = APIRouter(prefix="/admin", tags=["admin"])


class ReportReview(StrictModel):
    uid: str = Field(min_length=1, max_length=128)
    status: str = Field(pattern="^(pending|approved|needs_revision)$")
    comment: str = Field(default="", max_length=4000)


class SeedRequest(StrictModel):
    force: bool = False


@router.get("/overview")
async def overview(request: Request, _: Principal = Depends(admin_principal)):
    return await AnalyticsService(request.app.state.repository).overview()


@router.get("/users")
async def users(request: Request, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                q: str = Query("", max_length=100), _: Principal = Depends(admin_principal)):
    return await UserService(request.app.state.repository, request.app.state.settings).list_users(offset, limit, q)


@router.patch("/users/{uid}/role")
async def set_role(uid: str, payload: RoleUpdate, request: Request,
                   principal: Principal = Depends(admin_principal)):
    users = UserService(request.app.state.repository, request.app.state.settings)
    before = await users.public_profile(uid)
    after = await users.set_role(principal.uid, uid, payload.role)
    await AuditService(request.app.state.repository).record(
        principal.uid, "user.role_changed", f"users/{uid}", before, after, request_id_var.get())
    return {"user": after}


@router.get("/content/{collection}")
async def list_content(collection: str, request: Request, _: Principal = Depends(admin_principal)):
    return {"items": await request.app.state.content.list_collection(collection, include_unpublished=True)}


@router.post("/content/{collection}")
async def create_content(collection: str, payload: AdminContent, request: Request,
                         principal: Principal = Depends(admin_principal)):
    item = await request.app.state.content.upsert_admin(collection, None, payload, principal.uid)
    await AuditService(request.app.state.repository).record(
        principal.uid, "content.created", f"curriculum/{collection}/{item['id']}", None, item, request_id_var.get())
    return {"item": item}


@router.put("/content/{collection}/{item_id}")
async def update_content(collection: str, item_id: str, payload: AdminContent, request: Request,
                         principal: Principal = Depends(admin_principal)):
    content: ContentService = request.app.state.content
    before = await content.get_item(collection, item_id, include_unpublished=True)
    item = await content.upsert_admin(collection, item_id, payload, principal.uid)
    await AuditService(request.app.state.repository).record(
        principal.uid, "content.updated", f"curriculum/{collection}/{item_id}", before, item, request_id_var.get())
    return {"item": item}


@router.patch("/content/{collection}/{item_id}/publish")
async def publish_content(collection: str, item_id: str, payload: ContentPublish, request: Request,
                          principal: Principal = Depends(admin_principal)):
    content: ContentService = request.app.state.content
    before = await content.get_item(collection, item_id, include_unpublished=True)
    item = await content.set_published(collection, item_id, payload.published)
    await AuditService(request.app.state.repository).record(
        principal.uid, "content.published" if payload.published else "content.unpublished",
        f"curriculum/{collection}/{item_id}", before, item, request_id_var.get())
    return {"item": item}


@router.get("/assessments")
async def assessment_results(request: Request, offset: int = Query(0, ge=0),
                             limit: int = Query(50, ge=1, le=200), _: Principal = Depends(admin_principal)):
    return await AnalyticsService(request.app.state.repository).assessment_results(offset, limit)


@router.get("/reports")
async def reports(request: Request, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                  status: str = Query("", max_length=30), _: Principal = Depends(admin_principal)):
    return await ReportService(request.app.state.repository, request.app.state.content).list_all(offset, limit, status)


@router.patch("/reports/{report_id}/review")
async def review_report(report_id: str, payload: ReportReview, request: Request,
                        principal: Principal = Depends(admin_principal)):
    service = ReportService(request.app.state.repository, request.app.state.content)
    before = await request.app.state.repository.get(f"reports/{payload.uid}/{report_id}")
    after = await service.review(report_id, payload.uid, payload.status, payload.comment, principal.uid)
    await AuditService(request.app.state.repository).record(
        principal.uid, "report.reviewed", f"reports/{payload.uid}/{report_id}", before, after, request_id_var.get())
    return {"report": after}


@router.get("/audit")
async def audit(request: Request, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                _: Principal = Depends(admin_principal)):
    return await AuditService(request.app.state.repository).list(offset, limit)


@router.post("/content-seed")
async def seed_content(payload: SeedRequest, request: Request, principal: Principal = Depends(admin_principal)):
    counts = await request.app.state.content.seed(force=payload.force)
    await AuditService(request.app.state.repository).record(
        principal.uid, "content.seeded", "curriculum", None, counts, request_id_var.get())
    return {"status": "ok", "counts": counts, "force": payload.force}
