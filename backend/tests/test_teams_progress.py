def test_team_create_persist(client, student_headers):
    res = client.post("/api/teams", json={"name": "فريق أسيوط"}, headers=student_headers)
    assert res.status_code == 200
    team = res.json()["team"]
    assert team["name"] == "فريق أسيوط"
    assert len(team["virtual_member_ids"]) == 3
    again = client.get("/api/teams/mine", headers=student_headers)
    assert again.json()["team"]["id"] == team["id"]
    dup = client.post("/api/teams", json={"name": "فريق آخر"}, headers=student_headers)
    assert dup.status_code == 409


def test_team_name_validation(client, student_headers):
    assert client.post("/api/teams", json={"name": "a"}, headers=student_headers).status_code == 422
    assert client.post("/api/teams", json={"name": "<script>"}, headers=student_headers).status_code == 422


def test_team_name_unique(client, student_headers, admin_headers):
    assert client.post("/api/teams", json={"name": "فريق مشترك"}, headers=student_headers).status_code == 200
    assert client.post("/api/teams", json={"name": "فريق مشترك"}, headers=admin_headers).status_code == 409


def test_progress_empty_then_complete(client, student_headers, chapter_data):
    assert client.get("/api/progress", headers=student_headers).json()["progress"] == {}
    lesson = chapter_data["lessons"][0]
    exercise_answer = lesson["exercise"]["answer"]
    answers = [{"question_id": q["id"], "answer": q["answer"]} for q in lesson["assessment"]["questions"]]
    res = client.post(f"/api/progress/lessons/{lesson['id']}/complete",
                      json={"exercise_answer": exercise_answer, "assessment": {"answers": answers}},
                      headers=student_headers)
    assert res.status_code == 200, res.text
    assert res.json()["assessment"]["passed"] is True
    progress = client.get("/api/progress", headers=student_headers).json()["progress"]
    assert lesson["id"] in progress["lessons"]
    dashboard = client.get("/api/progress/dashboard", headers=student_headers).json()
    assert dashboard["overall"]["completed_lessons"] == 1
    assert dashboard["overall"]["percentage"] > 0


def test_complete_lesson_wrong_exercise(client, student_headers, chapter_data):
    lesson = chapter_data["lessons"][0]
    answers = [{"question_id": q["id"], "answer": q["answer"]} for q in lesson["assessment"]["questions"]]
    res = client.post(f"/api/progress/lessons/{lesson['id']}/complete",
                      json={"exercise_answer": "wrong", "assessment": {"answers": answers}},
                      headers=student_headers)
    assert res.status_code == 422


def test_assessment_scoring_and_history(client, student_headers, chapter_data):
    assessment = chapter_data["lessons"][1]["assessment"]
    answers = [{"question_id": q["id"], "answer": q["answer"]} for q in assessment["questions"]]
    res = client.post(f"/api/progress/assessments/{assessment['id']}/submit", json={"answers": answers}, headers=student_headers)
    assert res.status_code == 200
    assert res.json()["attempt"]["percentage"] == 100
    attempts = client.get("/api/progress/attempts", headers=student_headers).json()["items"]
    assert len(attempts) == 1


def test_assessment_missing_answer(client, student_headers):
    res = client.post("/api/progress/assessments/ch01_l01_as/submit", json={"answers": []}, headers=student_headers)
    assert res.status_code == 422


def test_enrollment(client, student_headers):
    res = client.post("/api/progress/enroll/ch01", json={}, headers=student_headers)
    assert res.status_code == 200
    assert res.json()["enrollment"]["chapter_id"] == "ch01"
