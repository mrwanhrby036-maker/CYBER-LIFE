from fastapi import APIRouter, Depends, Request
from app.dependencies import current_principal, Principal
from app.schemas import TeamCreate
from app.service_teams import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


def service(request: Request) -> TeamService:
    return TeamService(request.app.state.repository, request.app.state.content)


@router.get("/mine")
async def my_team(request: Request, principal: Principal = Depends(current_principal)):
    team = await service(request).get_team(principal.uid)
    return {"team": team, "teammates": await service(request).teammates() if team else []}


@router.post("")
async def create_team(payload: TeamCreate, request: Request, principal: Principal = Depends(current_principal)):
    return {"team": await service(request).create_team(principal.uid, payload.name)}


@router.get("/teammates")
async def teammates(request: Request, _: Principal = Depends(current_principal)):
    return {"items": await service(request).teammates()}
