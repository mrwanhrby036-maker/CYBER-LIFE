def test_chapters_exact_15(client, student_headers):
    res = client.get("/api/curriculum/chapters", headers=student_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 15
    assert [c["order"] for c in items] == list(range(1, 16))


def test_lessons_45(client, student_headers):
    res = client.get("/api/curriculum/lessons", headers=student_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 45


def test_invalid_lesson(client, student_headers):
    assert client.get("/api/curriculum/lessons/not_real", headers=student_headers).status_code == 404


def test_lesson_no_answer_keys(client, student_headers):
    res = client.get("/api/curriculum/lessons/ch01_l01", headers=student_headers)
    assert res.status_code == 200
    lesson = res.json()["lesson"]
    assert "answer" not in lesson["exercise"]
    assert "answer" not in lesson["assessment"] if "assessment" in lesson else True
    assert lesson["related_lessons"]


def test_assessment_public_no_keys(client, student_headers):
    res = client.get("/api/curriculum/assessments/ch01_l01_as", headers=student_headers)
    assert res.status_code == 200
    for q in res.json()["assessment"]["questions"]:
        assert "answer" not in q
        assert "accepted" not in q
        assert "rubric" not in q


def test_search(client, student_headers):
    res = client.get("/api/curriculum/search?q=سجل", headers=student_headers)
    assert res.status_code == 200
    assert res.json()["lessons"]


def test_glossary(client, student_headers):
    res = client.get("/api/curriculum/glossary", headers=student_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 50


def test_chapter_detail(client, student_headers):
    res = client.get("/api/curriculum/chapters/ch01", headers=student_headers)
    assert res.status_code == 200
    assert len(res.json()["lessons"]) == 3
