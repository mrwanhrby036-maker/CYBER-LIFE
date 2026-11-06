"""Persistent student teams with three explicitly simulated virtual colleagues."""
from app.helpers import utc_now, safe_key, normalize_answer
from app.errors import ConflictError, NotFoundError, ValidationError
from app.service_activity import ActivityService


class TeamService:
    def __init__(self, repository, content):
        self.repo = repository
        self.content = content
        self.activity = ActivityService(repository)

    async def get_team(self, uid: str) -> dict | None:
        team_id = await self.repo.get(f"users/{safe_key(uid)}/team_id")
        if not team_id:
            return None
        team = await self.repo.get(f"teams/{safe_key(team_id)}")
        if not team:
            raise NotFoundError("الفريق غير موجود")
        return team

    async def create_team(self, uid: str, name: str) -> dict:
        existing = await self.get_team(uid)
        if existing:
            raise ConflictError("اسم الفريق ثابت بعد إنشائه؛ لديك فريق بالفعل")
        normalized = normalize_answer(name)
        if len(normalized) < 3:
            raise ValidationError("اسم الفريق قصير جداً")
        teammates = await self.content.list_collection("teammates")
        if len(teammates) != 3:
            raise ValidationError("محتوى الزملاء الافتراضيين غير مكتمل")
        team_id = f"team_{uid}"
        # Reserve a normalized name atomically so two students cannot claim it.
        reservation_path = f"team_names/{normalized.replace(' ', '_')}"
        def reserve(current):
            if current is not None:
                raise ConflictError("اسم الفريق مستخدم بالفعل")
            return {"team_id": team_id, "owner_uid": uid, "created_at": utc_now()}
        await self.repo.transaction(reservation_path, reserve)
        team = {"id": team_id, "name": name, "owner_uid": uid, "created_at": utc_now(),
                "member_uids": [uid], "virtual_member_ids": [t["id"] for t in teammates],
                "contributions": [], "mission_history": []}
        try:
            await self.repo.set(f"teams/{team_id}", team)
            await self.repo.update(f"users/{safe_key(uid)}", {"team_id": team_id})
        except Exception:
            await self.repo.delete(reservation_path)
            raise
        await self.activity.record(uid, "team_created", f"أنشأت فريق {name}", team_id)
        return team

    async def teammates(self) -> list[dict]:
        return await self.content.list_collection("teammates")

    async def record_contribution(self, uid: str, mission_id: str, teammate_id: str,
                                  kind: str, text: str, evidence_ids=None) -> dict:
        team = await self.get_team(uid)
        if not team:
            raise ConflictError("أنشئ فريقك أولاً")
        if teammate_id not in team["virtual_member_ids"]:
            raise ValidationError("زميل غير تابع للفريق")
        contribution = {"mission_id": mission_id, "teammate_id": teammate_id,
                        "kind": kind, "text": text, "evidence_ids": evidence_ids or [],
                        "created_at": utc_now(), "simulated": True}
        def append(current):
            rows = current if isinstance(current, list) else []
            return (rows + [contribution])[-200:]
        await self.repo.transaction(f"teams/{team['id']}/contributions", append)
        return contribution
