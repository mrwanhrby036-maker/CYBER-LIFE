"""Per-user activity feed. Dashboard reads only the bounded recent_activity list."""
from app.helpers import utc_now


class ActivityService:
    def __init__(self, repository):
        self.repo = repository

    async def record(self, uid: str, kind: str, title: str, target: str = "", score=None) -> None:
        event = {"kind": kind, "title": title, "target": target,
                 "score": score, "created_at": utc_now()}
        await self.repo.push(f"activity/{uid}", event)
        def append(current):
            rows = current if isinstance(current, list) else []
            return (rows + [event])[-20:]
        await self.repo.transaction(f"users/{uid}/recent_activity", append)
