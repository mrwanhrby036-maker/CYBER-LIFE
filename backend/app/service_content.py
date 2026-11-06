"""Curriculum content loaded from versioned JSON into RTDB, then served from DB.

Public lesson payloads never contain answer keys. Admin edits live in the same
curriculum nodes and are audited by the router. Seeding never overwrites edits.
"""
import json
from pathlib import Path
from app.errors import NotFoundError, ValidationError, ConflictError
from app.helpers import safe_key, utc_now

SCHEMA_VERSION = 1
COLLECTIONS = {"chapters", "lessons", "assessments", "missions", "laboratory", "glossary", "teammates"}


def strip_question(question: dict) -> dict:
    return {k: v for k, v in question.items() if k not in {"answer", "accepted", "rubric", "explanation"}}


def strip_assessment(assessment: dict) -> dict:
    return {k: v for k, v in assessment.items() if k != "questions"} | {
        "questions": [strip_question(q) for q in assessment.get("questions", [])]}


class ContentService:
    def __init__(self, repository, content_dir: Path):
        self.repo = repository
        self.directory = Path(content_dir)

    def _load(self, relative: str):
        path = self.directory / relative
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    async def seed(self, force: bool = False) -> dict:
        """Idempotent import. force is an explicit admin operation, not startup."""
        counts = {}
        chapter_files = sorted(self.directory.glob("chapter-*.json"))
        if len(chapter_files) != 15:
            raise ValidationError("المنهج يحتاج خمسة عشر ملف فصل بالضبط")
        for file in chapter_files:
            chapter = self._load(file.name)
            self.validate_chapter(chapter)
            cid = chapter["id"]
            lesson_ids = []
            for lesson in chapter["lessons"]:
                lid = lesson["id"]
                lesson_ids.append(lid)
                public = {k: v for k, v in lesson.items() if k not in {"assessment", "exercise"}}
                public["chapter_id"] = cid
                public["assessment_id"] = lesson["assessment"]["id"]
                public["exercise"] = strip_question(lesson["exercise"])
                await self._seed_node(f"curriculum/lessons/{lid}", public, force)
                await self._seed_node(f"assessment_keys/lessons/{lid}", {
                    "exercise": lesson["exercise"], "assessment": lesson["assessment"]}, force)
                await self._seed_node(f"curriculum/assessments/{lesson['assessment']['id']}",
                                      strip_assessment(lesson["assessment"]) | {"chapter_id": cid, "lesson_id": lid, "kind": "lesson"}, force)
            public_chapter = {k: v for k, v in chapter.items() if k not in {"lessons", "chapter_assessment"}}
            public_chapter["lesson_ids"] = lesson_ids
            public_chapter["assessment_id"] = chapter["chapter_assessment"]["id"]
            await self._seed_node(f"curriculum/chapters/{cid}", public_chapter, force)
            await self._seed_node(f"curriculum/assessments/{chapter['chapter_assessment']['id']}",
                                  strip_assessment(chapter["chapter_assessment"]) | {"chapter_id": cid, "kind": "chapter"}, force)
            await self._seed_node(f"assessment_keys/chapters/{cid}", chapter["chapter_assessment"], force)
            counts["chapters"] = counts.get("chapters", 0) + 1
            counts["lessons"] = counts.get("lessons", 0) + len(lesson_ids)
        for collection, filename in [("missions", "missions.json"),
                                     ("laboratory", "laboratory.json"),
                                     ("glossary", "glossary.json"),
                                     ("teammates", "teammates.json")]:
            data = self._load(filename)
            items = data if isinstance(data, list) else data.get("items", [])
            for item in items:
                await self._seed_node(f"curriculum/{collection}/{safe_key(item['id'])}", item, force)
            counts[collection] = len(items)
        await self.repo.update("platform_settings", {"schema_version": SCHEMA_VERSION,
                                                    "seeded_at": utc_now(), "content_version": "1.0.0"})
        return counts

    async def _seed_node(self, path: str, value: dict, force: bool) -> None:
        existing = await self.repo.get(path)
        if existing is None or force:
            value = dict(value)
            value.setdefault("published", True)
            value.setdefault("created_at", utc_now())
            value["updated_at"] = utc_now()
            await self.repo.set(path, value)

    def validate_chapter(self, chapter: dict) -> None:
        required = {"id", "order", "title", "description", "lessons", "chapter_assessment"}
        if not required <= set(chapter):
            raise ValidationError("بيانات الفصل ناقصة")
        safe_key(chapter["id"])
        if not 1 <= int(chapter["order"]) <= 15:
            raise ValidationError("ترتيب الفصل خارج النطاق")
        if len(chapter["lessons"]) < 2:
            raise ValidationError("كل فصل يحتوي درسين على الأقل")
        for lesson in chapter["lessons"]:
            self.validate_lesson(lesson)
        self.validate_assessment(chapter["chapter_assessment"])

    def validate_lesson(self, lesson: dict) -> None:
        required = {"id", "title", "objectives", "introduction", "sections", "terminology",
                    "examples", "common_mistakes", "important_notes", "exercise",
                    "assessment", "references", "completion_criterion"}
        missing = required - set(lesson)
        if missing:
            raise ValidationError("حقول الدرس ناقصة", details={"missing": sorted(missing)})
        safe_key(lesson["id"])
        if len(lesson["sections"]) < 2 or len(lesson["objectives"]) < 2:
            raise ValidationError("الدرس يحتاج شرحاً وأهدافاً متعددة")
        self.validate_question(lesson["exercise"])
        self.validate_assessment(lesson["assessment"])

    def validate_assessment(self, assessment: dict) -> None:
        if not assessment.get("id") or not assessment.get("questions"):
            raise ValidationError("التقييم يحتاج معرّفاً وأسئلة")
        ids = [q["id"] for q in assessment["questions"]]
        if len(ids) != len(set(ids)):
            raise ValidationError("معرّفات الأسئلة مكررة")
        for question in assessment["questions"]:
            self.validate_question(question)

    def validate_question(self, question: dict) -> None:
        kind = question.get("type")
        if kind not in {"mcq", "multi", "short", "log", "command", "classification", "risk", "report"}:
            raise ValidationError("نوع السؤال غير مدعوم")
        if not question.get("id") or not question.get("prompt"):
            raise ValidationError("السؤال يحتاج معرّفاً ونصاً")
        if kind in {"mcq", "multi", "log", "command", "classification", "risk"}:
            options = question.get("options", [])
            if len(options) < 2:
                raise ValidationError("السؤال يحتاج اختيارين على الأقل")
            ids = [o["id"] for o in options]
            answers = question.get("answer", []) if kind == "multi" else [question.get("answer")]
            if not answers or any(a not in ids for a in answers):
                raise ValidationError("مفتاح الإجابة لا يطابق الاختيارات")
        elif kind == "short" and not question.get("answer"):
            raise ValidationError("السؤال القصير يحتاج مفتاح إجابة")
        elif kind == "report" and not question.get("rubric"):
            raise ValidationError("التقرير يحتاج معيار تقييم صريح")

    async def list_chapters(self, include_unpublished=False) -> list[dict]:
        nodes = await self.repo.get("curriculum/chapters", {})
        rows = [v for v in nodes.values() if include_unpublished or v.get("published")]
        return sorted(rows, key=lambda c: c["order"])

    async def get_chapter(self, chapter_id: str, include_unpublished=False) -> dict:
        chapter = await self.repo.get(f"curriculum/chapters/{safe_key(chapter_id)}")
        if not chapter or (not chapter.get("published") and not include_unpublished):
            raise NotFoundError("الفصل غير موجود أو غير منشور")
        return chapter

    async def get_lesson(self, lesson_id: str, include_unpublished=False) -> dict:
        lesson = await self.repo.get(f"curriculum/lessons/{safe_key(lesson_id)}")
        if not lesson or (not lesson.get("published") and not include_unpublished):
            raise NotFoundError("الدرس غير موجود أو غير منشور")
        chapter = await self.get_chapter(lesson["chapter_id"], include_unpublished)
        return lesson | {"related_lessons": [lid for lid in chapter["lesson_ids"] if lid != lesson_id]}

    async def list_lessons(self, chapter_id: str | None = None, query: str = "",
                           include_unpublished=False) -> list[dict]:
        nodes = await self.repo.get("curriculum/lessons", {})
        rows = []
        for lesson in nodes.values():
            if not include_unpublished and not lesson.get("published"):
                continue
            if chapter_id and lesson["chapter_id"] != chapter_id:
                continue
            if query:
                haystack = f"{lesson['title']} {lesson['introduction']} {' '.join(t['term'] for t in lesson['terminology'])}".lower()
                if query.lower() not in haystack:
                    continue
            rows.append({k: lesson[k] for k in ("id", "title", "chapter_id", "published", "estimated_minutes", "assessment_id") if k in lesson})
        return sorted(rows, key=lambda l: l["id"])

    async def get_assessment(self, assessment_id: str) -> dict:
        assessment = await self.repo.get(f"curriculum/assessments/{safe_key(assessment_id)}")
        if not assessment:
            raise NotFoundError("التقييم غير موجود")
        return assessment

    async def get_answer_key(self, assessment_id: str) -> dict:
        assessment = await self.get_assessment(assessment_id)
        if assessment["kind"] == "lesson":
            keys = await self.repo.get(f"assessment_keys/lessons/{assessment['lesson_id']}")
            return keys["assessment"] if keys else None
        keys = await self.repo.get(f"assessment_keys/chapters/{assessment['chapter_id']}")
        return keys

    async def get_exercise_key(self, lesson_id: str) -> dict:
        keys = await self.repo.get(f"assessment_keys/lessons/{safe_key(lesson_id)}")
        if not keys:
            raise NotFoundError("التمرين غير موجود")
        return keys["exercise"]

    async def list_collection(self, collection: str, include_unpublished=False) -> list[dict]:
        if collection not in COLLECTIONS:
            raise ValidationError("مجموعة غير معروفة")
        nodes = await self.repo.get(f"curriculum/{collection}", {})
        rows = [v for v in nodes.values() if include_unpublished or v.get("published", True)]
        return sorted(rows, key=lambda x: x.get("order", x.get("id", "")))

    async def get_item(self, collection: str, item_id: str, include_unpublished=False) -> dict:
        if collection not in COLLECTIONS:
            raise ValidationError("مجموعة غير معروفة")
        item = await self.repo.get(f"curriculum/{collection}/{safe_key(item_id)}")
        if not item or (not item.get("published", True) and not include_unpublished):
            raise NotFoundError("العنصر غير موجود أو غير منشور")
        return item

    async def search(self, query: str) -> dict:
        query = query.strip().lower()
        if len(query) < 2:
            raise ValidationError("اكتب حرفين على الأقل للبحث")
        lessons = await self.list_lessons(query=query)
        glossary = [g for g in await self.list_collection("glossary")
                    if query in f"{g['term']} {g['definition']}".lower()]
        return {"lessons": lessons[:30], "glossary": glossary[:30]}

    def validate_mission(self, mission: dict) -> None:
        required = ["title", "priority", "company_background", "incident_description",
                    "scope_authorization", "evidence", "investigation_questions", "answer_key", "evaluation"]
        missing = [k for k in required if k not in mission]
        if missing:
            raise ValidationError("حقول المهمة ناقصة", {"missing": missing})
        if mission["priority"] not in ("low", "medium", "high", "critical"):
            raise ValidationError("أولوية غير صالحة")
        if "decisions" not in mission.get("answer_key", {}):
            raise ValidationError("مفتاح إجابات المهمة ناقص")

    def validate_laboratory(self, scenario: dict) -> None:
        required = ["title", "objectives", "network", "filesystem", "exercises"]
        missing = [k for k in required if k not in scenario]
        if missing:
            raise ValidationError("حقول السيناريو ناقصة", {"missing": missing})
        for ex in scenario.get("exercises", []):
            v = ex.get("validation", {})
            if v.get("type") not in {"command", "any_of", "sequence"}:
                raise ValidationError("نوع تحقق غير معروف", {"exercise": ex.get("id")})

    def validate_teammate(self, teammate: dict) -> None:
        for key in ("name", "role", "specialty", "behavior"):
            if key not in teammate:
                raise ValidationError("بيانات الزميل ناقصة", {"missing": key})

    def validate_glossary(self, term: dict) -> None:
        for key in ("term", "definition", "chapter_id"):
            if key not in term:
                raise ValidationError("المصطلح ناقص", {"missing": key})

    async def upsert_admin(self, collection: str, item_id: str | None, payload, actor_uid: str) -> dict:
        if collection not in COLLECTIONS:
            raise ValidationError("مجموعة غير معروفة")
        item_id = safe_key(item_id) if item_id else None
        data = dict(payload.data)
        data.update({"title": payload.title, "description": payload.description,
                     "published": payload.published, "updated_at": utc_now(), "updated_by": actor_uid})
        if collection == "chapters":
            if item_id is None:
                data.setdefault("order", 99)
                data.setdefault("lesson_ids", [])
                data.setdefault("estimated_minutes", 0)
                data["published"] = False  # الفصول الجديدة مسودات؛ النشر محكوم بحد 15 فصلاً منشوراً
            else:
                existing = await self.get_chapter(item_id, include_unpublished=True)
                data = existing | data
                data["id"] = item_id
            data.pop("lessons", None)
            data.pop("chapter_assessment", None)
        elif collection == "lessons":
            if item_id:
                existing = await self.get_lesson(item_id, include_unpublished=True)
                data = existing | data
                data["id"] = item_id
            data.setdefault("chapter_id", "ch01")
            await self.get_chapter(data["chapter_id"], include_unpublished=True)
            # افصل مفاتيح الإجابة عن المحتوى العام دائماً
            assessment = data.pop("assessment", None)
            exercise = data.pop("exercise", None)
            if "sections" in data and assessment and exercise:
                candidate = data | {"id": item_id or data.get("id", "new_lesson"),
                                    "assessment": assessment, "exercise": exercise}
                self.validate_lesson(candidate)
                lid = item_id or data.get("id")
                if not lid:
                    from app.helpers import new_id
                    lid = new_id("less")
                    data["id"] = lid
                await self.repo.set(f"assessment_keys/lessons/{lid}", {"exercise": exercise, "assessment": assessment})
                await self.repo.set(f"curriculum/assessments/{assessment['id']}",
                                    strip_assessment(assessment) | {"chapter_id": data["chapter_id"], "lesson_id": lid, "kind": "lesson", "published": data.get("published", False)})
                data["assessment_id"] = assessment["id"]
                data["exercise"] = strip_question(exercise)
            elif "sections" in data:
                # تحرير حقول عامة دون مفاتيح جديدة: تحقق من الحقول الأساسية فقط
                for field in ("title", "objectives", "introduction", "sections", "terminology", "examples", "common_mistakes", "important_notes", "references", "completion_criterion"):
                    if field not in data:
                        raise ValidationError(f"حقل الدرس ناقص: {field}")
            if item_id is None and "id" not in data:
                from app.helpers import new_id
                data["id"] = new_id("less")
        elif collection == "assessments":
            if "questions" in data:
                self.validate_assessment(data | {"id": item_id or data.get("id", "new_assessment")})
                keys = {"id": item_id or data["id"], "questions": data["questions"],
                        "passing_score": data.get("passing_score", 70)}
                public = strip_assessment(data)
                kind = data.get("kind", "lesson")
                if kind == "lesson":
                    await self.repo.set(f"assessment_keys/lessons/{data['lesson_id']}/assessment", keys)
                else:
                    await self.repo.set(f"assessment_keys/chapters/{data['chapter_id']}", keys)
                data = public | {"kind": kind}
        elif collection == "missions":
            self.validate_mission(data)
        elif collection == "laboratory":
            self.validate_laboratory(data)
        elif collection == "teammates":
            self.validate_teammate(data)
        elif collection == "glossary":
            self.validate_glossary(data)
        if item_id is None:
            from app.helpers import new_id
            item_id = new_id(collection[:4])
            data["id"] = item_id
            data["created_at"] = utc_now()
        await self.repo.set(f"curriculum/{collection}/{item_id}", data)
        if collection == "chapters" and "lesson_ids" not in data:
            lessons = await self.list_lessons(item_id, include_unpublished=True)
            await self.repo.update(f"curriculum/chapters/{item_id}", {"lesson_ids": [l["id"] for l in lessons]})
        return await self.get_item(collection, item_id, include_unpublished=True)

    async def set_published(self, collection: str, item_id: str, published: bool) -> dict:
        await self.get_item(collection, item_id, include_unpublished=True)
        if collection == "chapters" and published:
            chapters = await self.list_chapters(include_unpublished=True)
            published_count = sum(1 for c in chapters if c.get("published") and c["id"] != item_id)
            if published_count >= 15:
                raise ConflictError("المنهج الأساسي يجب أن يحتوي 15 فصلاً منشوراً بالضبط؛ ألغِ نشر فصل آخر أولاً")
        if published and collection == "lessons":
            lesson = await self.get_lesson(item_id, include_unpublished=True)
            for field in ("title", "objectives", "introduction", "sections", "terminology",
                          "examples", "common_mistakes", "important_notes", "exercise",
                          "assessment_id", "references", "completion_criterion"):
                if field not in lesson:
                    raise ValidationError("لا يمكن نشر درس ناقص", {"missing": field})
            if len(lesson["sections"]) < 2 or len(lesson["objectives"]) < 2:
                raise ValidationError("الدرس يحتاج شرحاً وأهدافاً متعددة قبل النشر")
            if not await self.repo.get(f"assessment_keys/lessons/{safe_key(item_id)}"):
                raise ValidationError("لا يمكن نشر درس بلا مفتاح تقييم محفوظ", {"lesson_id": item_id})
        if published and collection == "missions":
            mission = await self.get_item("missions", item_id, include_unpublished=True)
            self.validate_mission(mission)
            if not mission.get("evidence") or not mission.get("investigation_questions"):
                raise ValidationError("لا يمكن نشر مهمة بلا أدلة وأسئلة تحقيق")
        if published and collection == "laboratory":
            self.validate_laboratory(await self.get_item("laboratory", item_id, include_unpublished=True))
        await self.repo.update(f"curriculum/{collection}/{safe_key(item_id)}",
                               {"published": published, "updated_at": utc_now()})
        return await self.get_item(collection, item_id, include_unpublished=True)
