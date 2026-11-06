"""Request-scoped identity and server-side authorization dependencies."""
from dataclasses import dataclass
from fastapi import Request
from app.errors import AuthenticationError, AuthorizationError
from app.service_users import UserService


@dataclass
class Principal:
    uid: str
    profile: dict
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


async def get_repository(request: Request):
    return request.app.state.repository


async def current_principal(request: Request) -> Principal:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise AuthenticationError("يلزم تسجيل الدخول")
    token = header[7:].strip()
    if not token or len(token) > 8192:
        raise AuthenticationError("رمز الجلسة غير صالح")
    users = UserService(request.app.state.repository, request.app.state.settings,
                        request.app.state.local_tokens)
    if request.app.state.settings.auth_mode == "firebase":
        identity = await request.app.state.firebase_auth.verify(token)
        profile = await users.ensure_firebase_profile(identity)
    else:
        uid = request.app.state.local_tokens.verify(token)
        profile = await users.get(uid)
        if not profile or not profile.get("active", True):
            raise AuthenticationError("الحساب غير متاح")
    role = await users.effective_role(profile["uid"])
    return Principal(uid=profile["uid"], profile=profile, role=role)


from fastapi import Depends


async def admin_principal(principal: Principal = Depends(current_principal)) -> Principal:
    if not principal.is_admin:
        raise AuthorizationError("صلاحيات الإدارة مطلوبة")
    return principal
