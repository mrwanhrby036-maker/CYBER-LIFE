"""Server-authoritative progress, enrollment and assessment history."""
from app.helpers import utc_now, safe_key
from app.errors import NotFoundError, ConflictError, ValidationError
from app.service_scoring import score_assessment, score_question
from app.service_activity import ActivityService


class ProgressService:
    def __init__(self, repository, content):
        self.repo = repository
        self.content = content
        self.activity = ActivityService(repository)

    async def enroll(self, uid: str, chapter_id: str) -> dict:
        chapter = await self.content.get_chapter(chapter_id)
        path = f"enrollments/{safe_key(uid)}/{safe_key(chapter_id)}"
        existing = await self.repo.get(path)
        if existing:
            return existing
        record = {"uid": uid, "chapter_id": chapter_id, "course_id": "cyber-life-core",
                  "status": "active", "enrolled_at": utc_now()}
        await self.repo.set(path, record)
        await self.activity.record(uid, "enrollment", f"التحققت بفصل {chapter['title']}", chapter_id)
        return record

    async def get_progress(self, uid: str) -> dict:
        return await self.repo.get(f"progress/{safe_key(uid)}", {})

    async def get_attempts(self, uid: str) -> list[dict]:
        nodes = await self.repo.get(f"assessments/{safe_key(uid)}", {})
        rows = [{"id": k, **v} for k, v in nodes.items()]
        return sorted(rows, key=lambda r: r["created_at"], reverse=True)

    async def submit_assessment(self, uid: str, assessment_id: str, submission) -> dict:
        public = await self.content.get_assessment(assessment_id)
        key = await self.content.get_answer_key(assessment_id)
        if not key:
            raise NotFoundError("مفتاح التقييم غير متاح")
        result = score_assessment(key, submission.answers)
        attempt = result | {"uid": uid, "chapter_id": public.get("chapter_id"),
                            "lesson_id": public.get("lesson_id"), "kind": public["kind"],
                            "created_at": utc_now()}
        attempt_id = await self.repo.push(f"assessments/{safe_key(uid)}", attempt)
        await self.activity.record(uid, "assessment", public.get("title", "تقييم"), assessment_id, result["percentage"])
        return attempt | {"id": attempt_id}

    async def complete_lesson(self, uid: str, lesson_id: str, payload) -> dict:
        lesson = await self.content.get_lesson(lesson_id)
        exercise_key = await self.content.get_exercise_key(lesson_id)
        exercise_result = score_question(exercise_key, payload.exercise_answer)
        if not exercise_result["correct"]:
            raise ValidationError("أكمل التمرين العملي بإجابة صحيحة قبل إنهاء الدرس",
                                  details={"exercise": exercise_result})
        assessment_id = lesson["assessment_id"]
        key = await self.content.get_answer_key(assessment_id)
        assessment_result = score_assessment(key, payload.assessment.answers)
        if not assessment_result["passed"]:
            # Preserve the failed attempt for learning history; do not mark complete.
            await self.repo.push(f"assessments/{safe_key(uid)}", assessment_result | {
                "uid": uid, "lesson_id": lesson_id, "chapter_id": lesson["chapter_id"],
                "kind": "lesson", "created_at": utc_now()})
            raise ValidationError("لم تبلغ درجة الاجتياز؛ راجع التغذية الراجعة وحاول مجدداً",
                                  details={"assessment": assessment_result})
        await self.enroll(uid, lesson["chapter_id"])
        attempt_id = await self.repo.push(f"assessments/{safe_key(uid)}", assessment_result | {
            "uid": uid, "lesson_id": lesson_id, "chapter_id": lesson["chapter_id"],
            "kind": "lesson", "created_at": utc_now()})
        record = {"lesson_id": lesson_id, "chapter_id": lesson["chapter_id"],
                  "status": "completed", "exercise_score": exercise_result["earned"],
                  "assessment_score": assessment_result["percentage"], "attempt_id": attempt_id,
                  "completed_at": utc_now()}
        await self.repo.set(f"progress/{safe_key(uid)}/lessons/{safe_key(lesson_id)}", record)
        await self.activity.record(uid, "lesson_completed", lesson["title"], lesson_id, assessment_result["percentage"])
        from app.service_achievements import AchievementService
        await AchievementService(self.repo).evaluate(uid)
        return {"lesson": record, "exercise": exercise_result, "assessment": assessment_result}

    async def dashboard(self, uid: str) -> dict:
        chapters = await self.content.list_chapters()
        lessons = await self.content.list_lessons()
        progress = await self.get_progress(uid)
        completed = progress.get("lessons", {})
        attempts = await self.get_attempts(uid)
        enrollments = await self.repo.get(f"enrollments/{safe_key(uid)}", {})
        team_id = (await self.repo.get(f"users/{safe_key(uid)}/team_id"))
        team = await self.repo.get(f"teams/{team_id}") if team_id else None
        missions = await self.repo.get(f"mission_submissions/{safe_key(uid)}", {})
        achievements = await self.repo.get(f"achievements/{safe_key(uid)}", {})
        profile = await self.repo.get(f"users/{safe_key(uid)}", {})
        total = len(lessons)
        done = len(completed)
        chapter_rows = []
        for chapter in chapters:
            chapter_lessons = [l for l in lessons if l["chapter_id"] == chapter["id"]]
            chapter_done = sum(l["id"] in completed for l in chapter_lessons)
            chapter_rows.append({"id": chapter["id"], "title": chapter["title"], "order": chapter["order"],
                                 "total": len(chapter_lessons), "completed": chapter_done,
                                 "percentage": round(100 * chapter_done / max(1, len(chapter_lessons)), 1)})
        current = next((c for c in chapter_rows if c["completed"] < c["total"]), chapter_rows[-1] if chapter_rows else None)
        current_lesson = next((l for l in lessons if l["id"] not in completed), None)
        weak = [a for a in attempts if a["percentage"] < 70][:5]
        review = []
        for attempt in weak:
            lesson = next((l for l in lessons if l["id"] == attempt.get("lesson_id")), None)
            if lesson and lesson["id"] not in [r["id"] for r in review]:
                review.append(lesson)
        mission_rows = [{"id": k, "state": v.get("state"), "title": v.get("title", k)} for k, v in missions.items()]
        return {"profile": {k: v for k, v in profile.items() if k not in {"password_hash", "recent_activity"}},
                "team": team, "current_chapter": current, "current_lesson": current_lesson,
                "overall": {"total_lessons": total, "completed_lessons": done,
                            "pending_lessons": total - done,
                            "percentage": round(100 * done / max(1, total), 1)},
                "chapters": chapter_rows, "scores": [{"id": a["id"], "title": a["title"],
                                                       "percentage": a["percentage"], "passed": a["passed"],
                                                       "created_at": a["created_at"]} for a in attempts[:10]],
                "missions": mission_rows, "achievements": list(achievements.values()),
                "recent_activity": profile.get("recent_activity", [])[-10:][::-1],
                "review_lessons": review, "enrollments": list(enrollments.values()),
                "learning_history": attempts[:20]}
