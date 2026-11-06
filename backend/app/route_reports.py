from fastapi import APIRouter, Depends, Request
from app.dependencies import current_principal, Principal
from app.schemas import ReportSubmission
from app.service_reports import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def service(request: Request) -> ReportService:
    return ReportService(request.app.state.repository, request.app.state.content)


@router.get("")
async def list_reports(request: Request, principal: Principal = Depends(current_principal)):
    return {"items": await service(request).list_mine(principal.uid)}


@router.post("")
async def submit(payload: ReportSubmission, request: Request, principal: Principal = Depends(current_principal)):
    return {"report": await service(request).submit(principal.uid, payload)}


@router.get("/{report_id}")
async def get_report(report_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return {"report": await service(request).get_mine(principal.uid, report_id)}
