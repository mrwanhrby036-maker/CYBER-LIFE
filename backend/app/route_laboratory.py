from fastapi import APIRouter, Depends, Request
from app.dependencies import current_principal, Principal
from app.schemas import LabCommand, LabValidation
from app.service_laboratory import LaboratoryService, ALLOWED_COMMANDS

router = APIRouter(prefix="/laboratory", tags=["laboratory"])


def service(request: Request) -> LaboratoryService:
    return LaboratoryService(request.app.state.repository, request.app.state.content)


@router.get("/scenarios")
async def scenarios(request: Request, _: Principal = Depends(current_principal)):
    return {"items": await service(request).list_scenarios(), "allowed_commands": sorted(ALLOWED_COMMANDS)}


@router.get("/scenarios/{scenario_id}")
async def scenario(scenario_id: str, request: Request, principal: Principal = Depends(current_principal)):
    lab = service(request)
    return {"scenario": await lab.get_scenario(scenario_id),
            "session": await lab.session(principal.uid, scenario_id)}


@router.post("/scenarios/{scenario_id}/command")
async def command(scenario_id: str, payload: LabCommand, request: Request,
                  principal: Principal = Depends(current_principal)):
    return {"entry": await service(request).run_command(principal.uid, scenario_id, payload.command)}


@router.post("/scenarios/{scenario_id}/validate")
async def validate(scenario_id: str, payload: LabValidation, request: Request,
                   principal: Principal = Depends(current_principal)):
    return {"result": await service(request).validate_exercise(principal.uid, scenario_id, payload)}
