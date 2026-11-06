import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[2] / "content"


def test_lab_scenarios(client, student_headers):
    res = client.get("/api/laboratory/scenarios", headers=student_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 6
    assert "ls" in res.json()["allowed_commands"]


def test_lab_safe_command(client, student_headers):
    res = client.post("/api/laboratory/scenarios/lab01/command", json={"command": "pwd"}, headers=student_headers)
    assert res.status_code == 200
    assert res.json()["entry"]["output"] == "/home/analyst"


def test_lab_blocks_dangerous(client, student_headers):
    for cmd in ["rm -rf /", "cat /etc/passwd; whoami", "echo hi > file", "curl http://example.com", "python3 -c 'print(1)'"]:
        res = client.post("/api/laboratory/scenarios/lab01/command", json={"command": cmd}, headers=student_headers)
        assert res.status_code == 422, cmd


def test_lab_grep_count(client, student_headers):
    res = client.post("/api/laboratory/scenarios/lab02/command", json={"command": "grep -c Failed auth.log"}, headers=student_headers)
    assert res.status_code == 200
    assert res.json()["entry"]["output"] == "4"


def test_lab_validate_exercise(client, student_headers):
    for cmd in ["pwd", "ls -la", "cat readme.txt"]:
        client.post("/api/laboratory/scenarios/lab01/command", json={"command": cmd}, headers=student_headers)
    res = client.post("/api/laboratory/scenarios/lab01/validate",
                      json={"exercise_id": "lab01_ex1", "answers": [{"question_id": "q1", "answer": "pwd"}]},
                      headers=student_headers)
    assert res.status_code == 200
    assert res.json()["result"]["passed"] is True


def test_mission_workflow(client, student_headers):
    client.post("/api/teams", json={"name": "فريق المهام"}, headers=student_headers)
    mid = "mis01"
    assert client.post(f"/api/missions/{mid}/assign", json={}, headers=student_headers).status_code == 200
    assert client.post(f"/api/missions/{mid}/transition", json={"state": "investigating"}, headers=student_headers).status_code == 200
    mission = client.get(f"/api/missions/{mid}", headers=student_headers).json()["mission"]
    assert "answer_key" not in mission
    for ev in mission["evidence"]:
        if ev.get("required"):
            assert client.post(f"/api/missions/{mid}/evidence", json={"evidence_id": ev["id"]}, headers=student_headers).status_code == 200
    assert client.post(f"/api/missions/{mid}/transition", json={"state": "evidence_collected"}, headers=student_headers).status_code == 200
    ask = client.post(f"/api/missions/{mid}/ask", json={"teammate_id": "tm_researcher", "topic": "initial"}, headers=student_headers)
    assert ask.status_code == 200 and ask.json()["simulated"] is True
    missions = json.loads((CONTENT / "missions.json").read_text(encoding="utf-8"))
    m = next(x for x in missions if x["id"] == mid)
    for q in m["investigation_questions"]:
        ans = m["answer_key"]["decisions"][q["id"]]
        res = client.post(f"/api/missions/{mid}/decisions", json={"question_id": q["id"], "choice_id": ans,
                          "justification": "استندت إلى السجل الاصطناعي والدليل المطلوب."}, headers=student_headers)
        assert res.status_code == 200
    findings = "ظهرت محاولات فشل ثم نجاح. نوصي بالتحقق من هوية المستخدم ومراجعة السجلات وتفعيل MFA."
    actions = "تعطيل مؤقت عند الاشتباه، مراجعة سجل الهوية، وتوثيق الإجراءات في تقرير الحادث."
    assert client.post(f"/api/missions/{mid}/findings", json={"findings": findings, "actions": actions}, headers=student_headers).status_code == 200
    assert client.post(f"/api/missions/{mid}/transition", json={"state": "under_review"}, headers=student_headers).status_code == 200
    assert client.post(f"/api/missions/{mid}/transition", json={"state": "resolved"}, headers=student_headers).status_code == 200
    report = {"title": "تقرير مهمة الاختبار", "mission_id": mid,
              "summary": "تم رصد محاولات فشل ثم نجاح في سجل اصطناعي ضمن مهمة تدريبية مصرح بها.",
              "evidence": "السجل يظهر محاولات فاشلة ثم نجاحاً من عنوان مختلف مع طابع زمني واضح.",
              "analysis": "هذا يشير إلى نمط يستحق التحقق ولا يثبت اختراقاً؛ نحتاج مراجعة هوية المستخدم وسجل الهوية.",
              "actions": "نوصي بتفعيل MFA ومراجعة الصلاحيات وتعطيل الحساب مؤقتاً عند الاشتباه وتوثيق المتابعة."}
    res = client.post("/api/reports", json=report, headers=student_headers)
    assert res.status_code == 200, res.text
    assert client.post(f"/api/missions/{mid}/transition", json={"state": "closed"}, headers=student_headers).status_code == 200
    final = client.get(f"/api/missions/{mid}", headers=student_headers).json()["mission"]["submission"]
    assert final["state"] == "closed"
    assert final["score"] >= 70


def test_mission_cannot_skip(client, student_headers):
    client.post("/api/teams", json={"name": "فريق القفز"}, headers=student_headers)
    assert client.post("/api/missions/mis02/transition", json={"state": "closed"}, headers=student_headers).status_code == 409


def test_report_rubric(client, student_headers):
    report = {"title": "تقرير قصير", "summary": "تم رصد حادث اصطناعي في سجل التدريب.",
              "evidence": "السجل يظهر عنوان IP وطابع زمني ومحاولات دخول.",
              "analysis": "هذا يدل على نمط مشبوه لكنه غير مؤكد ويحتاج تحققاً.",
              "actions": "نوصي بعزل الجهاز ومراجعة الصلاحيات وتفعيل MFA."}
    res = client.post("/api/reports", json=report, headers=student_headers)
    assert res.status_code == 200
    assert res.json()["report"]["evaluation"]["method"] == "deterministic_rubric"


def test_admin_report_review(client, student_headers, admin_headers):
    report = {"title": "تقرير مراجعة", "summary": "تم رصد حادث اصطناعي في سجل التدريب.",
              "evidence": "السجل يظهر عنوان IP وطابع زمني ومحاولات دخول.",
              "analysis": "هذا يدل على نمط مشبوه لكنه غير مؤكد ويحتاج تحققاً.",
              "actions": "نوصي بعزل الجهاز ومراجعة الصلاحيات وتفعيل MFA."}
    rid = client.post("/api/reports", json=report, headers=student_headers).json()["report"]["id"]
    res = client.patch(f"/api/admin/reports/{rid}/review", json={"uid": "dev_student", "status": "approved", "comment": "جيد"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["report"]["review"]["status"] == "approved"
