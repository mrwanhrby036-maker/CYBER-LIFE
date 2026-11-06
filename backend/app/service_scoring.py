"""Deterministic assessment scoring. No AI grading is claimed or performed.

Objective questions use exact option IDs or normalized accepted answers.
Open responses use explicit concept-group rubrics and required evidence IDs;
length alone never earns points. Every result includes per-question feedback.
"""
from app.helpers import normalize_answer
from app.errors import ValidationError


def _as_list(value) -> list[str]:
    return value if isinstance(value, list) else [value]


def score_question(question: dict, answer) -> dict:
    qid = question["id"]
    kind = question["type"]
    points = float(question.get("points", 1))
    earned = 0.0
    feedback = ""
    correct = False
    if kind in {"mcq", "log", "command", "classification", "risk"}:
        if not isinstance(answer, str):
            raise ValidationError(f"السؤال {qid} يحتاج إجابة واحدة")
        correct = answer.strip() == str(question["answer"])
        earned = points if correct else 0
        feedback = question.get("explanation", "أعد قراءة الدليل المرتبط بالسؤال.")
    elif kind == "multi":
        if not isinstance(answer, list) or any(not isinstance(x, str) for x in answer):
            raise ValidationError(f"السؤال {qid} يحتاج قائمة اختيارات")
        expected = set(question["answer"])
        selected = set(answer)
        if len(selected) != len(answer):
            raise ValidationError("لا تكرر الاختيارات")
        # Partial credit with a penalty for incorrect selections, floored at zero.
        hits = len(expected & selected)
        false_positives = len(selected - expected)
        ratio = max(0.0, (hits - false_positives) / max(1, len(expected)))
        earned = round(points * ratio, 3)
        correct = selected == expected
        feedback = question.get("explanation", "قارن كل اختيار بالدليل.")
    elif kind == "short":
        if not isinstance(answer, str):
            raise ValidationError(f"السؤال {qid} يحتاج نصاً")
        normalized = normalize_answer(answer)
        accepted = [normalize_answer(x) for x in question.get("accepted", [question["answer"]])]
        correct = normalized in accepted
        earned = points if correct else 0
        feedback = question.get("explanation", "استخدم المصطلح التقني المحدد في الدرس.")
    elif kind == "report":
        if not isinstance(answer, str):
            raise ValidationError(f"السؤال {qid} يحتاج تقريراً نصياً")
        normalized = normalize_answer(answer)
        rubric = question.get("rubric", [])
        if not rubric:
            raise ValidationError("سؤال التقرير بلا معيار تقييم")
        criteria = []
        total_weight = sum(float(c.get("weight", 1)) for c in rubric)
        for criterion in rubric:
            groups = criterion.get("any_of", [])
            matched = any(any(normalize_answer(term) in normalized for term in group) for group in groups)
            weight = float(criterion.get("weight", 1))
            if matched:
                earned += weight
            criteria.append({"id": criterion["id"], "label": criterion["label"],
                             "met": matched, "points": weight if matched else 0,
                             "max_points": weight})
        earned = round(points * earned / max(1, total_weight), 3)
        correct = earned >= points * float(question.get("pass_ratio", 0.7))
        feedback = "تقييم آلي بمعيار معلن، وليس ذكاءً اصطناعياً. " + question.get("explanation", "")
        return {"question_id": qid, "type": kind, "earned": earned, "points": points,
                "correct": correct, "feedback": feedback, "rubric": criteria,
                "answer": answer}
    else:
        raise ValidationError("نوع سؤال غير مدعوم")
    return {"question_id": qid, "type": kind, "earned": earned, "points": points,
            "correct": correct, "feedback": feedback, "answer": answer}


def score_assessment(assessment: dict, submissions: list) -> dict:
    questions = assessment["questions"]
    by_id = {q["id"]: q for q in questions}
    answers = {}
    for item in submissions:
        qid = item.question_id if hasattr(item, "question_id") else item["question_id"]
        answer = item.answer if hasattr(item, "answer") else item["answer"]
        if qid not in by_id:
            raise ValidationError("معرف سؤال لا ينتمي إلى هذا التقييم")
        if qid in answers:
            raise ValidationError("لا تكرر إجابة السؤال")
        answers[qid] = answer
    missing = set(by_id) - set(answers)
    if missing:
        raise ValidationError("أجب عن جميع الأسئلة قبل التسليم", details={"missing": sorted(missing)})
    results = [score_question(q, answers[q["id"]]) for q in questions]
    total = sum(float(q.get("points", 1)) for q in questions)
    earned = round(sum(r["earned"] for r in results), 3)
    percentage = round(100 * earned / max(1, total), 2)
    passing = float(assessment.get("passing_score", 70))
    return {"assessment_id": assessment["id"], "title": assessment.get("title", "تقييم"),
            "earned": earned, "total": total, "percentage": percentage,
            "passed": percentage >= passing, "passing_score": passing,
            "results": results, "method": "deterministic_rubric"}
