def test_admin_requires_role(client, student_headers):
    assert client.get("/api/admin/overview", headers=student_headers).status_code == 403
    assert client.get("/api/admin/users", headers=student_headers).status_code == 403


def test_admin_overview(client, admin_headers):
    res = client.get("/api/admin/overview", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["chapters"] == 15
    assert res.json()["lessons"] == 45


def test_admin_role_change_audited(client, admin_headers, student_headers):
    me = client.get("/api/auth/me", headers=student_headers).json()["user"]
    res = client.patch(f"/api/admin/users/{me['uid']}/role", json={"role": "admin"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "admin"
    audit = client.get("/api/admin/audit", headers=admin_headers).json()["items"]
    assert any(a["action"] == "user.role_changed" for a in audit)
    # restore
    client.patch(f"/api/admin/users/{me['uid']}/role", json={"role": "student"}, headers=admin_headers)


def test_admin_cannot_self_demote(client, admin_headers):
    res = client.patch("/api/admin/users/dev_admin/role", json={"role": "student"}, headers=admin_headers)
    assert res.status_code == 409


def test_admin_publish_unpublish(client, admin_headers, student_headers):
    res = client.patch("/api/admin/content/lessons/ch01_l01/publish", json={"published": False}, headers=admin_headers)
    assert res.status_code == 200
    assert client.get("/api/curriculum/lessons/ch01_l01", headers=student_headers).status_code == 404
    assert client.get("/api/admin/content/lessons", headers=admin_headers).status_code == 200
    client.patch("/api/admin/content/lessons/ch01_l01/publish", json={"published": True}, headers=admin_headers)
    assert client.get("/api/curriculum/lessons/ch01_l01", headers=student_headers).status_code == 200


def test_admin_invalid_collection(client, admin_headers):
    assert client.get("/api/admin/content/unknown", headers=admin_headers).status_code == 422


def test_admin_content_create_mission(client, admin_headers):
    payload = {"title": "مهمة اختبار", "description": "وصف", "published": False,
               "data": {"id": "mis_test", "order": 99, "identifier": "CL-TEST", "chapter_id": "ch01", "priority": "low",
                        "company_background": "خلفية", "incident_description": "وصف حادث",
                        "scope_authorization": "تفويض", "evidence": [], "teammate_comments": [],
                        "investigation_questions": [], "answer_key": {"decisions": {}},
                        "evaluation": {"passing_score": 70, "findings_rubric": []}}}
    res = client.post("/api/admin/content/missions", json=payload, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["item"]["published"] is False


def test_student_cannot_seed(client, student_headers):
    assert client.post("/api/admin/content-seed", json={"force": True}, headers=student_headers).status_code == 403


def test_rate_limit_shape(client, student_headers):
    res = client.get("/api/curriculum/chapters", headers=student_headers)
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"
