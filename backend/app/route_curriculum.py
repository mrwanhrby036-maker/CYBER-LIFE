from fastapi import APIRouter, Depends, Query, Request
from app.dependencies import current_principal, Principal
from app.service_content import ContentService

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


def service(request: Request) -> ContentService:
    return request.app.state.content


@router.get("/chapters")
async def chapters(request: Request, _: Principal = Depends(current_principal)):
    return {"items": await service(request).list_chapters()}


@router.get("/chapters/{chapter_id}")
async def chapter(chapter_id: str, request: Request, _: Principal = Depends(current_principal)):
    content = service(request)
    chapter = await content.get_chapter(chapter_id)
    lessons = await content.list_lessons(chapter_id)
    return {"chapter": chapter, "lessons": lessons}


@router.get("/lessons")
async def lessons(request: Request, chapter_id: str | None = None, q: str = Query(default="", max_length=100),
                  _: Principal = Depends(current_principal)):
    return {"items": await service(request).list_lessons(chapter_id, q)}


@router.get("/lessons/{lesson_id}")
async def lesson(lesson_id: str, request: Request, _: Principal = Depends(current_principal)):
    return {"lesson": await service(request).get_lesson(lesson_id)}


@router.get("/assessments/{assessment_id}")
async def assessment(assessment_id: str, request: Request, _: Principal = Depends(current_principal)):
    return {"assessment": await service(request).get_assessment(assessment_id)}


@router.get("/glossary")
async def glossary(request: Request, _: Principal = Depends(current_principal)):
    return {"items": await service(request).list_collection("glossary")}


@router.get("/search")
async def search(request: Request, q: str = Query(min_length=2, max_length=100),
                 _: Principal = Depends(current_principal)):
    return await service(request).search(q)
