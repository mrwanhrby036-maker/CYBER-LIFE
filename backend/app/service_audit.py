"""Append-only administrative audit records; secrets are never logged."""
from app.helpers import utc_now
from app.logging_setup import redact


class AuditService:
    def __init__(self, repository):
        self.repo = repository

    async def record(self, actor_uid: str, action: str, target: str,
                     before=None, after=None, request_id: str = "-") -> str:
        entry = {"actor_uid": actor_uid, "action": action, "target": target,
                 "before": redact(before), "after": redact(after),
                 "request_id": request_id, "created_at": utc_now()}
        return await self.repo.push("audit_logs", entry)

    async def list(self, offset: int = 0, limit: int = 50) -> dict:
        from app.helpers import paginate
        records = await self.repo.get("audit_logs", {})
        rows = [{"id": key, **value} for key, value in records.items()]
        rows.sort(key=lambda row: row["created_at"], reverse=True)
        return paginate(rows, offset, limit)
