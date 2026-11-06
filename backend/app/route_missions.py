from fastapi import APIRouter, Depends, Request
from pydantic import Field
from app.dependencies import current_principal, Principal
from app.schemas import StrictModel, MissionDecision, MissionFindings, MissionTransition
from app.service_missions import MissionService

router = APIRouter(prefix="/missions", tags=["missions"])


class EvidenceRequest(StrictModel):
    evidence_id: str = Field(min_length=1, max_length=128)


class AskRequest(StrictModel):
    teammate_id: str = Field(min_length=1, max_length=128)
    topic: str = Field(default="", max_length=128)


def service(request: Request) -> MissionService:
    return MissionService(request.app.state.repository, request.app.state.content)


@router.get("")
async def list_missions(request: Request, principal: Principal = Depends(current_principal)):
    return {"items": await service(request).list_missions(principal.uid)}


@router.get("/{mission_id}")
async def get_mission(mission_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return {"mission": await service(request).get_mission(principal.uid, mission_id)}


@router.post("/{mission_id}/assign")
async def assign(mission_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return {"submission": await service(request).assign(principal.uid, mission_id)}


@router.post("/{mission_id}/evidence")
async def collect(mission_id: str, payload: EvidenceRequest, request: Request,
                  principal: Principal = Depends(current_principal)):
    return {"submission": await service(request).collect_evidence(principal.uid, mission_id, payload.evidence_id)}


@router.post("/{mission_id}/ask")
async def ask(mission_id: str, payload: AskRequest, request: Request,
              principal: Principal = Depends(current_principal)):
    return await service(request).ask_teammate(principal.uid, mission_id, payload.teammate_id, payload.topic)


@router.post("/{mission_id}/decisions")
async def decide(mission_id: str, payload: MissionDecision, request: Request,
                 principal: Principal = Depends(current_principal)):
    return {"submission": await service(request).decide(principal.uid, mission_id, payload)}


@router.post("/{mission_id}/findings")
async def findings(mission_id: str, payload: MissionFindings, request: Request,
                   principal: Principal = Depends(current_principal)):
    return {"submission": await service(request).findings(principal.uid, mission_id, payload)}


@router.post("/{mission_id}/transition")
async def transition(mission_id: str, payload: MissionTransition, request: Request,
                     principal: Principal = Depends(current_principal)):
    return {"submission": await service(request).transition(principal.uid, mission_id, payload.state)}
