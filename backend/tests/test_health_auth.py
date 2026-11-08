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


def test_auth_me_cors_preflight_for_configured_vercel_origin(client):
    response = client.options(
        "/api/auth/me",
        headers={
            "Origin": "https://cyber-life-wheat.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://cyber-life-wheat.vercel.app"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_invalid_login(client):
    res = client.post("/api/auth/local/login", json={"email": "student@cyberlife.local", "password": "wrong-password-123"})
    assert res.status_code == 401


def test_login_and_me_returns_safe_profile(client, student_token):
    import asyncio
    asyncio.run(client.app.state.repository.update("users/dev_student", {
        "private_notes": "do not expose", "service_account": "must stay private"
    }))
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    user = res.json()["user"]
    assert user["role"] == "student"
    assert user["uid"] == "dev_student"
    assert user["email"] == "student@cyberlife.local"
    assert "password_hash" not in user
    assert "private_notes" not in user


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
