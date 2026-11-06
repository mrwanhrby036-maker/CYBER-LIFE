from fastapi import APIRouter, Depends, Request
from app.dependencies import current_principal, Principal
from app.service_achievements import AchievementService

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("")
async def my_achievements(request: Request, principal: Principal = Depends(current_principal)):
    service = AchievementService(request.app.state.repository)
    return {"items": await service.list(principal.uid), "catalog": await service.catalog()}
