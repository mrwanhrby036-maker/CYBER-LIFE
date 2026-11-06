from fastapi import APIRouter, Depends, Request
from app.dependencies import current_principal, Principal
from app.schemas import AssessmentSubmission, LessonCompletion
from app.service_progress import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])


def service(request: Request) -> ProgressService:
    return ProgressService(request.app.state.repository, request.app.state.content)


@router.get("")
async def get_progress(request: Request, principal: Principal = Depends(current_principal)):
    return {"progress": await service(request).get_progress(principal.uid)}


@router.get("/dashboard")
async def dashboard(request: Request, principal: Principal = Depends(current_principal)):
    return await service(request).dashboard(principal.uid)


@router.get("/attempts")
async def attempts(request: Request, principal: Principal = Depends(current_principal)):
    return {"items": await service(request).get_attempts(principal.uid)}


@router.post("/enroll/{chapter_id}")
async def enroll(chapter_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return {"enrollment": await service(request).enroll(principal.uid, chapter_id)}


@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, payload: LessonCompletion, request: Request,
                          principal: Principal = Depends(current_principal)):
    return await service(request).complete_lesson(principal.uid, lesson_id, payload)


@router.post("/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id: str, payload: AssessmentSubmission, request: Request,
                            principal: Principal = Depends(current_principal)):
    return {"attempt": await service(request).submit_assessment(principal.uid, assessment_id, payload)}
