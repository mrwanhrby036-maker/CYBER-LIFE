"""Incident reports with deterministic rubric feedback and admin review."""
from app.helpers import utc_now, safe_key, normalize_answer, paginate
from app.errors import NotFoundError, ValidationError
from app.service_activity import ActivityService

DEFAULT_RUBRIC = [
    {"id": "summary", "label": "ملخص واضح للحادث", "weight": 1,
     "any_of": [["ملخص", "وقع", "حادث", "تم رصد"]]},
    {"id": "evidence", "label": "أدلة محددة", "weight": 2,
     "any_of": [["سجل", "دليل", "log", "عنوان", "ip", "ملف", "طابع زمني"]]},
    {"id": "analysis", "label": "تحليل يربط الدليل بالاستنتاج", "weight": 2,
     "any_of": [["يشير", "يدل", "نستنتج", "بسبب", "يؤكد", "يتوافق"]]},
    {"id": "actions", "label": "إجراءات احتواء ومعالجة", "weight": 2,
     "any_of": [["عزل", "احتواء", "حظر", "تعطيل", "إبلاغ", "مراجعة", "تحديث", "كلمة مرور"]]},
    {"id": "limits", "label": "حدود الثقة أو الأدلة الناقصة", "weight": 1,
     "any_of": [["غير مؤكد", "افتراض", "فرضية", "لا يؤكد", "نحتاج", "حدود", "غير متاح"]]},
]


class ReportService:
    def __init__(self, repository, content):
        self.repo = repository
        self.content = content
        self.activity = ActivityService(repository)

    def evaluate(self, text: str, rubric=None) -> dict:
        rubric = rubric or DEFAULT_RUBRIC
        normalized = normalize_answer(text)
        criteria = []
        for criterion in rubric:
            met = any(any(normalize_answer(term) in normalized for term in group) for group in criterion["any_of"])
            criteria.append({"id": criterion["id"], "label": criterion["label"], "met": met,
                             "weight": criterion.get("weight", 1)})
        total = sum(c["weight"] for c in criteria) or 1
        earned = sum(c["weight"] for c in criteria if c["met"])
        percentage = round(100 * earned / total, 2)
        return {"percentage": percentage, "passed": percentage >= 70, "criteria": criteria,
                "method": "deterministic_rubric",
                "notice": "تقييم آلي بمعيار معلن وليس ذكاءً اصطناعياً؛ المراجعة البشرية متاحة للإدارة."}

    async def submit(self, uid: str, payload) -> dict:
        if payload.mission_id:
            await self.content.get_item("missions", payload.mission_id)
            sub = await self.repo.get(f"mission_submissions/{safe_key(uid)}/{safe_key(payload.mission_id)}")
            if not sub:
                raise ValidationError("استلم المهمة قبل إرفاق تقرير بها")
        text = "\n".join([payload.summary, payload.evidence, payload.analysis, payload.actions])
        rubric = None
        if payload.mission_id:
            mission = await self.content.get_item("missions", payload.mission_id)
            rubric = mission.get("evaluation", {}).get("report_rubric")
        evaluation = self.evaluate(text, rubric)
        report = {"title": payload.title, "summary": payload.summary, "evidence": payload.evidence,
                  "analysis": payload.analysis, "actions": payload.actions,
                  "mission_id": payload.mission_id or None, "uid": uid,
                  "evaluation": evaluation, "review": {"status": "pending", "comment": "", "reviewer_uid": None},
                  "created_at": utc_now(), "updated_at": utc_now()}
        report_id = await self.repo.push(f"reports/{safe_key(uid)}", report)
        await self.activity.record(uid, "report_submitted", payload.title, report_id, evaluation["percentage"])
        if payload.mission_id:
            from app.service_missions import MissionService
            await MissionService(self.repo, self.content).attach_report(uid, payload.mission_id, report_id)
        return report | {"id": report_id}

    async def list_mine(self, uid: str) -> list[dict]:
        nodes = await self.repo.get(f"reports/{safe_key(uid)}", {})
        rows = [{"id": k, **v} for k, v in nodes.items()]
        return sorted(rows, key=lambda r: r["created_at"], reverse=True)

    async def get_mine(self, uid: str, report_id: str) -> dict:
        report = await self.repo.get(f"reports/{safe_key(uid)}/{safe_key(report_id)}")
        if not report:
            raise NotFoundError("التقرير غير موجود")
        return report | {"id": report_id}

    async def list_all(self, offset=0, limit=50, status="") -> dict:
        users = await self.repo.get("users", {})
        rows = []
        for uid in users:
            reports = await self.repo.get(f"reports/{uid}", {})
            for rid, report in reports.items():
                if status and report.get("review", {}).get("status") != status:
                    continue
                rows.append({"id": rid, "uid": uid, "student_name": users[uid].get("display_name", uid), **report})
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return paginate(rows, offset, limit)

    async def review(self, report_id: str, uid: str, status: str, comment: str, reviewer_uid: str) -> dict:
        if status not in {"pending", "approved", "needs_revision"}:
            raise ValidationError("حالة مراجعة غير صالحة")
        path = f"reports/{safe_key(uid)}/{safe_key(report_id)}"
        report = await self.repo.get(path)
        if not report:
            raise NotFoundError("التقرير غير موجود")
        review = {"status": status, "comment": comment, "reviewer_uid": reviewer_uid, "reviewed_at": utc_now()}
        await self.repo.update(path, {"review": review, "updated_at": utc_now()})
        return report | {"id": report_id, "review": review}
