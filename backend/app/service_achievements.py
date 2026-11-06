"""Achievement rules evaluated from persisted progress, missions, labs and reports."""
from __future__ import annotations
from app.helpers import utc_now, safe_key

RULES = [
    {"id": "first_lesson", "title": "الخطوة الأولى", "description": "أكملت أول درس بنجاح.", "icon": "spark"},
    {"id": "five_lessons", "title": "أساس متين", "description": "أكملت خمسة دروس.", "icon": "book"},
    {"id": "team_founder", "title": "روح الفريق", "description": "أنشأت فريقك الدائم.", "icon": "team"},
    {"id": "first_mission", "title": "أول مهمة مغلقة", "description": "أغلقت مهمة تحقيق وفق سير العمل.", "icon": "shield"},
    {"id": "lab_operator", "title": "مشغّل مختبر", "description": "اجتزت تمرين مختبر عملي.", "icon": "terminal"},
    {"id": "reporter", "title": "موثّق محترف", "description": "سلّمت تقرير حادث اجتاز المعيار.", "icon": "document"},
    {"id": "chapter_master", "title": "إتقان فصل", "description": "أكملت جميع دروس فصل واجتزت تقييمه.", "icon": "award"},
    {"id": "graduate", "title": "خريج CYBER LIFE", "description": "أكملت الدروس والمهام الخمسة عشر.", "icon": "trophy"},
]


class AchievementService:
    def __init__(self, repository):
        self.repo = repository

    async def evaluate(self, uid: str) -> list[dict]:
        uid = safe_key(uid)
        progress = await self.repo.get(f"progress/{uid}/lessons", {})
        missions = await self.repo.get(f"mission_submissions/{uid}", {})
        labs = await self.repo.get(f"lab_sessions/{uid}", {})
        reports = await self.repo.get(f"reports/{uid}", {})
        attempts = await self.repo.get(f"assessments/{uid}", {})
        team_id = await self.repo.get(f"users/{uid}/team_id")
        closed = sum(m.get("state") == "closed" for m in missions.values())
        lab_passed = any(s.get("completed_exercises") for s in labs.values())
        report_passed = any(r.get("evaluation", {}).get("passed") for r in reports.values())
        chapter_complete = False
        chapters = await self.repo.get("curriculum/chapters", {})
        for chapter in chapters.values():
            lids = chapter.get("lesson_ids", [])
            if lids and all(lid in progress for lid in lids):
                if any(a.get("kind") == "chapter" and a.get("chapter_id") == chapter["id"] and a.get("passed")
                       for a in attempts.values()):
                    chapter_complete = True
        conditions = {"first_lesson": len(progress) >= 1, "five_lessons": len(progress) >= 5,
                      "team_founder": bool(team_id), "first_mission": closed >= 1,
                      "lab_operator": lab_passed, "reporter": report_passed,
                      "chapter_master": chapter_complete,
                      "graduate": len(progress) >= 45 and closed >= 15}
        existing = await self.repo.get(f"achievements/{uid}", {})
        awarded = []
        for rule in RULES:
            if conditions[rule["id"]] and rule["id"] not in existing:
                record = rule | {"awarded_at": utc_now()}
                await self.repo.set(f"achievements/{uid}/{rule['id']}", record)
                awarded.append(record)
        return list(existing.values()) + awarded

    async def list(self, uid: str) -> list[dict]:
        await self.evaluate(uid)
        nodes = await self.repo.get(f"achievements/{safe_key(uid)}", {})
        return sorted(nodes.values(), key=lambda a: a["awarded_at"])

    async def catalog(self) -> list[dict]:
        return RULES
