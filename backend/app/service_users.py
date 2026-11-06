"""Profiles, verified-role resolution and account administration."""
from app.helpers import utc_now, safe_key, paginate
from app.errors import NotFoundError, ConflictError, AuthorizationError
from app.tokens import hash_password


class UserService:
    def __init__(self, repository, settings, local_tokens=None):
        self.repo = repository
        self.settings = settings
        self.local_tokens = local_tokens

    async def get(self, uid: str) -> dict | None:
        return await self.repo.get(f"users/{safe_key(uid)}")

    async def effective_role(self, uid: str) -> str:
        if uid in self.settings.bootstrap_admin_uids:
            return "admin"
        role = await self.repo.get(f"admin_roles/{safe_key(uid)}")
        return "admin" if role is True or (isinstance(role, dict) and role.get("enabled") is True) else "student"

    async def public_profile(self, uid: str) -> dict:
        profile = await self.get(uid)
        if not profile:
            raise NotFoundError("الحساب غير موجود")
        role = await self.effective_role(uid)
        return {k: v for k, v in profile.items() if k not in {"password_hash", "private_notes"}} | {"role": role}

    async def ensure_firebase_profile(self, identity) -> dict:
        path = f"users/{safe_key(identity.uid)}"
        def create(existing):
            if existing:
                if not existing.get("active", True):
                    raise AuthorizationError("الحساب موقوف")
                return existing | {"email": identity.email, "email_verified": identity.email_verified,
                                  "last_login_at": utc_now()}
            return {"uid": identity.uid, "email": identity.email,
                    "display_name": identity.name or "متعلم", "school": "", "governorate": "",
                    "role": "student", "active": True, "email_verified": identity.email_verified,
                    "created_at": utc_now(), "last_login_at": utc_now(), "team_id": None}
        return await self.repo.transaction(path, create)

    async def update_profile(self, uid: str, payload) -> dict:
        values = {"display_name": payload.display_name, "school": payload.school,
                  "governorate": payload.governorate, "updated_at": utc_now()}
        await self.repo.update(f"users/{safe_key(uid)}", values)
        return await self.public_profile(uid)

    async def initialize_local_accounts(self) -> None:
        if (self.settings.env != "development" or self.settings.auth_mode != "local"
                or not self.settings.enable_local_dev
                or not self.settings.dev_student_password or not self.settings.dev_admin_password):
            return
        accounts = [("dev_student", "student@cyberlife.local", "طالب تجريبي",
                     self.settings.dev_student_password),
                    ("dev_admin", "admin@cyberlife.local", "مدير تجريبي",
                     self.settings.dev_admin_password)]
        for uid, email, name, password in accounts:
            existing = await self.get(uid)
            if not existing:
                await self.repo.set(f"users/{uid}", {
                    "uid": uid, "email": email, "display_name": name, "school": "",
                    "governorate": "", "role": "student", "active": True,
                    "email_verified": True, "created_at": utc_now(), "team_id": None,
                    "password_hash": hash_password(password, n=self.settings.local_scrypt_n)})
        if not await self.repo.get("admin_roles/dev_admin"):
            await self.repo.set("admin_roles/dev_admin", True)

    async def local_login(self, email: str, password: str) -> tuple[str, int, dict]:
        # Development accounts are few and fixed. Firebase users never use this path.
        for uid in ("dev_student", "dev_admin"):
            profile = await self.get(uid)
            if profile and profile["email"].lower() == email.lower():
                from app.tokens import verify_password
                if verify_password(password, profile.get("password_hash", "")) and profile.get("active", True):
                    token, expires = self.local_tokens.issue(uid)
                    await self.repo.update(f"users/{uid}", {"last_login_at": utc_now()})
                    return token, expires, await self.public_profile(uid)
        # Equalize unknown-user and wrong-password work to reduce enumeration.
        from app.tokens import verify_password
        verify_password(password, hash_password("constant-work-decoy", n=self.settings.local_scrypt_n))
        raise AuthorizationError("بيانات الدخول غير صحيحة", status_code=401, code="invalid_credentials")

    async def list_users(self, offset: int, limit: int, query: str = "") -> dict:
        users = await self.repo.get("users", {})
        rows = []
        for uid, profile in users.items():
            if query and query.lower() not in f"{profile.get('display_name', '')} {profile.get('email', '')}".lower():
                continue
            rows.append({k: v for k, v in profile.items() if k != "password_hash"} |
                        {"role": await self.effective_role(uid)})
        rows.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return paginate(rows, offset, limit)

    async def set_role(self, actor_uid: str, target_uid: str, role: str) -> dict:
        safe_key(target_uid)
        if actor_uid == target_uid and role != "admin":
            raise ConflictError("لا يمكنك إزالة صلاحياتك الإدارية أثناء الجلسة")
        if target_uid in self.settings.bootstrap_admin_uids and role != "admin":
            raise ConflictError("أزل المعرّف من إعداد المديرين أولاً")
        await self.repo.set(f"admin_roles/{target_uid}", role == "admin")
        await self.repo.update(f"users/{target_uid}", {"role": role, "updated_at": utc_now()})
        return await self.public_profile(target_uid)
