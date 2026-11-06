"""Admin learning analytics computed from stored records, never fabricated."""
from collections import Counter
from app.helpers import paginate


class AnalyticsService:
    def __init__(self, repository):
        self.repo = repository

    async def overview(self) -> dict:
        users = await self.repo.get("users", {})
        chapters = await self.repo.get("curriculum/chapters", {})
        lessons = await self.repo.get("curriculum/lessons", {})
        progress = await self.repo.get("progress", {})
        assessments = await self.repo.get("assessments", {})
        missions = await self.repo.get("mission_submissions", {})
        reports = await self.repo.get("reports", {})
        total_students = sum(1 for u in users.values() if u.get("role") != "admin")
        completed_lessons = sum(len(p.get("lessons", {})) for p in progress.values())
        attempt_rows = [a for user_attempts in assessments.values() for a in user_attempts.values()]
        avg = round(sum(a["percentage"] for a in attempt_rows) / len(attempt_rows), 2) if attempt_rows else 0
        pass_rate = round(100 * sum(a["passed"] for a in attempt_rows) / len(attempt_rows), 2) if attempt_rows else 0
        mission_states = Counter(m.get("state", "new") for user_missions in missions.values() for m in user_missions.values())
        report_count = sum(len(r) for r in reports.values())
        pending_reports = sum(1 for user_reports in reports.values() for r in user_reports.values()
                              if r.get("review", {}).get("status") == "pending")
        chapter_stats = []
        for chapter in sorted(chapters.values(), key=lambda c: c.get("order", 0)):
            lids = chapter.get("lesson_ids", [])
            completions = sum(1 for p in progress.values() for lid in lids if lid in p.get("lessons", {}))
            possible = len(lids) * max(1, total_students)
            chapter_stats.append({"id": chapter["id"], "title": chapter["title"],
                                  "completions": completions,
                                  "completion_rate": round(100 * completions / possible, 2)})
        return {"students": total_students, "chapters": len(chapters), "lessons": len(lessons),
                "completed_lessons": completed_lessons, "assessment_attempts": len(attempt_rows),
                "average_score": avg, "pass_rate": pass_rate, "mission_states": dict(mission_states),
                "reports": report_count, "pending_reports": pending_reports,
                "chapter_stats": chapter_stats, "generated_from": "stored_records"}

    async def assessment_results(self, offset=0, limit=50) -> dict:
        users = await self.repo.get("users", {})
        assessments = await self.repo.get("assessments", {})
        rows = []
        for uid, attempts in assessments.items():
            for aid, attempt in attempts.items():
                rows.append({"id": aid, "uid": uid,
                             "student_name": users.get(uid, {}).get("display_name", uid),
                             "title": attempt.get("title"), "percentage": attempt.get("percentage"),
                             "passed": attempt.get("passed"), "kind": attempt.get("kind"),
                             "created_at": attempt.get("created_at")})
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return paginate(rows, offset, limit)
