import json
import shutil
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.config import Settings
from app.main import create_app

CONTENT = BACKEND.parent / "content"


@pytest.fixture(scope="session")
def seeded_template(tmp_path_factory):
    """Seed content once per test session; each test gets an isolated copy."""
    from app.db_local import LocalRepository
    from app.service_content import ContentService
    import asyncio
    directory = tmp_path_factory.mktemp("seeded")
    async def build():
        repo = LocalRepository(directory, fsync=False)
        await ContentService(repo, CONTENT).seed()
        await repo.close()
    asyncio.run(build())
    return directory / "database.json"


@pytest.fixture()
def settings(tmp_path, seeded_template):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(seeded_template, data_dir / "database.json")
    return Settings(
        env="development", auth_mode="local", storage_mode="local", enable_local_dev=True,
        data_dir=data_dir, content_dir=CONTENT,
        frontend_dir=BACKEND.parent / "frontend", serve_frontend=False,
        local_secret="test-secret-key-with-more-than-32-characters",
        dev_student_password="Student-Test-Password-123!",
        dev_admin_password="Admin-Test-Password-123!",
        rate_limit_per_minute=10000, auth_rate_limit_per_minute=100,
        local_fsync=False, local_scrypt_n=1024,
        cors_origins="https://cyber-life-wheat.vercel.app,http://localhost:8000",
    )


@pytest.fixture()
def app(settings):
    return create_app(settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c


def login(client, email="student@cyberlife.local", password="Student-Test-Password-123!"):
    res = client.post("/api/auth/local/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture()
def student_token(client):
    return login(client)


@pytest.fixture()
def admin_token(client):
    return login(client, "admin@cyberlife.local", "Admin-Test-Password-123!")


@pytest.fixture()
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def chapter_data():
    return json.loads((CONTENT / "chapter-01.json").read_text(encoding="utf-8"))
