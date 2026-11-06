"""Deterministic company-mission workflow with evidence-gated transitions.

Teammates are scripted educational characters, not LLM agents. Their comments
are labeled by epistemic status and may contain deliberate misconceptions.
"""
from app.helpers import utc_now, safe_key
from app.errors import NotFoundError, ConflictError, ValidationError, AuthorizationError
from app.service_teams import TeamService
from app.service_scoring import score_question
from app.service_activity import ActivityService

STATES = ["new", "assigned", "investigating", "evidence_collected", "under_review", "resolved", "closed"]
ALLOWED = {"new": {"assigned"}, "assigned": {"investigating"},
           "investigating": {"evidence_collected"}, "evidence_collected": {"under_review"},
           "under_review": {"resolved", "investigating"}, "resolved": {"closed"}, "closed": set()}


class MissionService:
    def __init__(self, repository, content):
        self.repo = repository
        self.content = content
        self.teams = TeamService(repository, content)
        self.activity = ActivityService(repository)

    async def list_missions(self, uid: str) -> list[dict]:
        missions = await self.content.list_collection("missions")
        submissions = await self.repo.get(f"mission_submissions/{safe_key(uid)}", {})
        rows = []
        for mission in missions:
            sub = submissions.get(mission["id"], {})
            rows.append({"id": mission["id"], "title": mission["title"], "chapter_id": mission["chapter_id"],
                         "priority": mission["priority"], "identifier": mission["identifier"],
                         "state": sub.get("state", "new"), "score": sub.get("score"),
                         "updated_at": sub.get("updated_at")})
        return rows

    async def get_mission(self, uid: str, mission_id: str) -> dict:
        mission = await self.content.get_item("missions", mission_id)
        sub = await self.repo.get(f"mission_submissions/{safe_key(uid)}/{safe_key(mission_id)}", {})
        # Evidence is available only after assignment; answer keys never leave server.
        public = {k: v for k, v in mission.items() if k not in {"answer_key", "evaluation"}}
        public["investigation_questions"] = [
            {k: v for k, v in q.items() if k != "explanation"}
            for q in public.get("investigation_questions", [])
        ]
        if sub.get("state", "new") in {"new"}:
            public["evidence"] = []
            public["teammate_comments"] = []
        else:
            collected = set(sub.get("collected_evidence", []))
            public["evidence"] = [e | {"collected": e["id"] in collected} for e in mission.get("evidence", [])]
            public["teammate_comments"] = mission.get("teammate_comments", [])
        public["submission"] = sub
        public["available_transitions"] = sorted(ALLOWED.get(sub.get("state", "new"), set()))
        return public

    async def _submission(self, uid: str, mission_id: str) -> dict:
        return await self.repo.get(f"mission_submissions/{safe_key(uid)}/{safe_key(mission_id)}", {})

    async def _save(self, uid: str, mission_id: str, values: dict) -> dict:
        values["updated_at"] = utc_now()
        await self.repo.update(f"mission_submissions/{safe_key(uid)}/{safe_key(mission_id)}", values)
        return await self._submission(uid, mission_id)

    async def assign(self, uid: str, mission_id: str) -> dict:
        mission = await self.content.get_item("missions", mission_id)
        team = await self.teams.get_team(uid)
        if not team:
            raise ConflictError("أنشئ فريقك قبل استلام المهام")
        sub = await self._submission(uid, mission_id)
        if sub:
            raise ConflictError("المهمة مسندة بالفعل")
        record = {"mission_id": mission_id, "uid": uid, "team_id": team["id"],
                  "title": mission["title"], "state": "assigned", "assigned_at": utc_now(),
                  "collected_evidence": [], "decisions": [], "findings": None,
                  "report_id": None, "score": None, "history": [
                      {"state": "assigned", "at": utc_now(), "by": uid}]}
        await self.repo.set(f"mission_submissions/{safe_key(uid)}/{safe_key(mission_id)}", record)
        await self.activity.record(uid, "mission_assigned", mission["title"], mission_id)
        return record

    async def collect_evidence(self, uid: str, mission_id: str, evidence_id: str) -> dict:
        mission = await self.content.get_item("missions", mission_id)
        sub = await self._submission(uid, mission_id)
        if sub.get("state") not in {"investigating", "evidence_collected"}:
            raise ConflictError("ابدأ التحقيق قبل جمع الأدلة")
        evidence = next((e for e in mission["evidence"] if e["id"] == evidence_id), None)
        if not evidence:
            raise NotFoundError("الدليل غير موجود في هذه المهمة")
        collected = list(dict.fromkeys(sub.get("collected_evidence", []) + [evidence_id]))
        return await self._save(uid, mission_id, {"collected_evidence": collected})

    async def ask_teammate(self, uid: str, mission_id: str, teammate_id: str, topic: str) -> dict:
        mission = await self.content.get_item("missions", mission_id)
        sub = await self._submission(uid, mission_id)
        if sub.get("state", "new") == "new":
            raise ConflictError("استلم المهمة أولاً")
        comments = [c for c in mission.get("teammate_comments", [])
                    if c["teammate_id"] == teammate_id and (not topic or c.get("topic") == topic)]
        if not comments:
            raise NotFoundError("لا توجد ملاحظة لهذا الزميل في هذا السياق")
        comment = comments[0]
        contribution = await self.teams.record_contribution(
            uid, mission_id, teammate_id, comment["status"], comment["text"], comment.get("evidence_ids"))
        return {"comment": comment, "contribution": contribution, "simulated": True}

    async def decide(self, uid: str, mission_id: str, payload) -> dict:
        mission = await self.content.get_item("missions", mission_id)
        sub = await self._submission(uid, mission_id)
        if sub.get("state") not in {"investigating", "evidence_collected", "under_review"}:
            raise ConflictError("التحقيق غير مفتوح للقرارات")
        question = next((q for q in mission["investigation_questions"] if q["id"] == payload.question_id), None)
        if not question:
            raise NotFoundError("سؤال التحقيق غير موجود")
        if payload.choice_id not in {o["id"] for o in question["options"]}:
            raise ValidationError("اختيار غير صالح")
        key = mission["answer_key"]["decisions"].get(payload.question_id)
        correct = payload.choice_id == key
        decision = {"question_id": payload.question_id, "choice_id": payload.choice_id,
                    "justification": payload.justification, "correct": correct,
                    "feedback": question.get("explanation", ""), "created_at": utc_now()}
        decisions = [d for d in sub.get("decisions", []) if d["question_id"] != payload.question_id] + [decision]
        return await self._save(uid, mission_id, {"decisions": decisions})

    async def findings(self, uid: str, mission_id: str, payload) -> dict:
        sub = await self._submission(uid, mission_id)
        if sub.get("state") not in {"evidence_collected", "under_review", "investigating"}:
            raise ConflictError("لا يمكن تسجيل النتائج في هذه المرحلة")
        findings = {"findings": payload.findings, "actions": payload.actions, "created_at": utc_now()}
        return await self._save(uid, mission_id, {"findings": findings})

    async def transition(self, uid: str, mission_id: str, target: str) -> dict:
        mission = await self.content.get_item("missions", mission_id)
        sub = await self._submission(uid, mission_id)
        state = sub.get("state", "new")
        if target not in ALLOWED.get(state, set()):
            raise ConflictError(f"لا يمكن الانتقال من {state} إلى {target}")
        if target == "evidence_collected":
            required = {e["id"] for e in mission["evidence"] if e.get("required")}
            if not required <= set(sub.get("collected_evidence", [])):
                raise ValidationError("اجمع الأدلة المطلوبة أولاً", details={"missing": sorted(required - set(sub.get("collected_evidence", [])))})
        if target == "under_review":
            answered = {d["question_id"] for d in sub.get("decisions", [])}
            required = {q["id"] for q in mission["investigation_questions"]}
            if not required <= answered:
                raise ValidationError("أجب عن أسئلة التحقيق كلها")
            if not sub.get("findings"):
                raise ValidationError("سجل النتائج والإجراءات المقترحة")
        if target == "resolved":
            evaluation = self.evaluate(mission, sub)
            if not evaluation["passed"]:
                raise ValidationError("لم تجتز معايير المهمة؛ راجع التغذية الراجعة", details=evaluation)
            await self._save(uid, mission_id, {"score": evaluation["percentage"], "evaluation": evaluation})
        if target == "closed":
            if not sub.get("report_id"):
                raise ValidationError("أرفق تقرير الحادث قبل الإغلاق")
            if sub.get("score") is None:
                raise ValidationError("لا يمكن الإغلاق قبل اجتياز التقييم")
        history = sub.get("history", []) + [{"state": target, "at": utc_now(), "by": uid}]
        result = await self._save(uid, mission_id, {"state": target, "history": history})
        await self.activity.record(uid, "mission_state", f"{mission['title']} → {target}", mission_id)
        if target == "closed":
            from app.service_achievements import AchievementService
            await AchievementService(self.repo).evaluate(uid)
        return result

    def evaluate(self, mission: dict, sub: dict) -> dict:
        decisions = {d["question_id"]: d for d in sub.get("decisions", [])}
        keys = mission["answer_key"]["decisions"]
        earned = sum(1 for qid, key in keys.items() if decisions.get(qid, {}).get("choice_id") == key)
        decision_pct = 100 * earned / max(1, len(keys))
        findings = sub.get("findings") or {}
        rubric = mission["evaluation"]["findings_rubric"]
        text = f"{findings.get('findings', '')} {findings.get('actions', '')}"
        from app.helpers import normalize_answer
        normalized = normalize_answer(text)
        met = []
        for criterion in rubric:
            ok = any(any(normalize_answer(term) in normalized for term in group) for group in criterion["any_of"])
            met.append({"id": criterion["id"], "label": criterion["label"], "met": ok, "weight": criterion.get("weight", 1)})
        total_weight = sum(c["weight"] for c in met) or 1
        findings_pct = 100 * sum(c["weight"] for c in met if c["met"]) / total_weight
        percentage = round(decision_pct * 0.6 + findings_pct * 0.4, 2)
        passing = mission["evaluation"].get("passing_score", 70)
        return {"percentage": percentage, "passed": percentage >= passing, "passing_score": passing,
                "decision_percentage": round(decision_pct, 2), "findings_percentage": round(findings_pct, 2),
                "rubric": met, "method": "deterministic_rubric"}

    async def attach_report(self, uid: str, mission_id: str, report_id: str) -> dict:
        sub = await self._submission(uid, mission_id)
        if sub.get("state") not in {"under_review", "resolved"}:
            raise ConflictError("أرفق التقرير أثناء المراجعة أو بعد الحل")
        report = await self.repo.get(f"reports/{safe_key(uid)}/{safe_key(report_id)}")
        if not report or report.get("mission_id") != mission_id:
            raise ValidationError("التقرير غير تابع لهذه المهمة")
        return await self._save(uid, mission_id, {"report_id": report_id})
