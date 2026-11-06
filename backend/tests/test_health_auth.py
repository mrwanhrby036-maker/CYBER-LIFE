from tests.conftest import login


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "auth_mode" not in data
    assert "storage_mode" not in data


def test_ready_seeded(client):
    res = client.get("/api/health/ready")
    assert res.status_code == 200
    assert res.json()["content_seeded"] is True


def test_unauthorized(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/curriculum/chapters").status_code == 401


def test_invalid_login(client):
    res = client.post("/api/auth/local/login", json={"email": "student@cyberlife.local", "password": "wrong-password-123"})
    assert res.status_code == 401


def test_login_and_me(client, student_token):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "student"


def test_admin_login_role(client, admin_token):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.json()["user"]["role"] == "admin"


def test_invalid_token(client):
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer local.fake.sig"}).status_code == 401


def test_profile_update_validation(client, student_headers):
    res = client.patch("/api/auth/profile", json={"display_name": "x"}, headers=student_headers)
    assert res.status_code == 422
    res = client.patch("/api/auth/profile", json={"display_name": "طالب اختبار", "school": "مدرسة", "governorate": "أسيوط"}, headers=student_headers)
    assert res.status_code == 200
    assert res.json()["user"]["display_name"] == "طالب اختبار"


def test_extra_fields_rejected(client, student_headers):
    res = client.patch("/api/auth/profile", json={"display_name": "طالب", "role": "admin"}, headers=student_headers)
    assert res.status_code == 422
