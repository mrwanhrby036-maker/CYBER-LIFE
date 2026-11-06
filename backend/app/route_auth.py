from fastapi import APIRouter, Depends, Request
from app.dependencies import current_principal, Principal
from app.schemas import LocalLogin, ProfileUpdate
from app.service_users import UserService
from app.errors import ConflictError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def me(principal: Principal = Depends(current_principal)):
    return {"user": principal.profile | {"role": principal.role}}


@router.post("/local/login")
async def local_login(payload: LocalLogin, request: Request):
    settings = request.app.state.settings
    if (settings.env != "development" or settings.auth_mode != "local"
            or not settings.enable_local_dev):
        raise ConflictError("تسجيل الدخول غير متاح بهذه الطريقة")
    users = UserService(request.app.state.repository, settings, request.app.state.local_tokens)
    token, expires, profile = await users.local_login(payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer", "expires_at": expires,
            "user": profile, "mode": "local-development",
            "notice": "جلسة تطوير حقيقية موقعة؛ ليست Firebase ولا تعمل في الإنتاج."}


@router.post("/logout")
async def logout(principal: Principal = Depends(current_principal)):
    # State bearer tokens are discarded client-side; Firebase revocation is handled
    # by Firebase Auth signOut. Local tokens expire and are not accepted after exp.
    return {"status": "ok", "message": "امسح الرمز من العميل وأنهِ جلسة Firebase عند استخدامه."}


@router.patch("/profile")
async def update_profile(payload: ProfileUpdate, request: Request,
                         principal: Principal = Depends(current_principal)):
    users = UserService(request.app.state.repository, request.app.state.settings)
    return {"user": await users.update_profile(principal.uid, payload)}
