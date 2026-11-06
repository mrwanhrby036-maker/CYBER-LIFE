"""Validated configuration; secrets never leave this module through public APIs."""
from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CYBERLIFE_", env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8", extra="ignore", case_sensitive=False,
    )
    env: str = "development"
    auth_mode: str = "local"
    storage_mode: str = "local"
    data_dir: Path = BASE_DIR / ".data"
    content_dir: Path = BASE_DIR.parent / "content"
    frontend_dir: Path = BASE_DIR.parent / "frontend"
    serve_frontend: bool = True
    log_level: str = "INFO"
    local_secret: str = ""
    local_token_hours: int = Field(default=8, ge=1, le=24)
    enable_local_dev: bool = False
    dev_student_password: str = ""
    dev_admin_password: str = ""
    firebase_project_id: str = "hamo-8132e"
    firebase_database_url: str = ""
    firebase_credentials_file: str = ""
    firebase_credentials_json: str = ""
    admin_uids: str = ""
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000"
    cors_origin_regex: str = ""
    rate_limit_per_minute: int = Field(default=180, ge=10, le=10000)
    auth_rate_limit_per_minute: int = Field(default=15, ge=3, le=100)
    max_body_bytes: int = Field(default=262144, ge=1024, le=2097152)
    max_report_chars: int = Field(default=16000, ge=1000, le=50000)
    local_fsync: bool = True
    local_scrypt_n: int = Field(default=16384, ge=1024, le=1048576)

    @field_validator("env")
    @classmethod
    def known_env(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"development", "production"}:
            raise ValueError("env must be development or production")
        return value

    @field_validator("auth_mode", "storage_mode")
    @classmethod
    def known_mode(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"local", "firebase"}:
            raise ValueError("Mode must be local or firebase")
        return value

    @field_validator("firebase_database_url")
    @classmethod
    def secure_database_url(cls, value: str) -> str:
        if value and not value.startswith("https://"):
            raise ValueError("Realtime Database URL must use HTTPS")
        return value.rstrip("/")

    @model_validator(mode="after")
    def fail_closed_production(self):
        if self.env == "production":
            if self.auth_mode != "firebase" or self.storage_mode != "firebase":
                raise ValueError("Production requires Firebase auth AND Firebase storage")
            if not self.cors_origins.strip() or "*" in self.cors_origins:
                raise ValueError("Production requires explicit HTTPS CORS origins")
            if any(not x.startswith("https://") for x in self.origins):
                raise ValueError("Production CORS origins must use HTTPS")
        if self.auth_mode == "firebase" or self.storage_mode == "firebase":
            if not self.firebase_database_url or not self.firebase_project_id:
                raise ValueError("Firebase database URL and project ID are required")
            if not (self.firebase_credentials_file or self.firebase_credentials_json):
                raise ValueError("Firebase service-account credentials are required")
        if self.env == "production" and self.serve_frontend:
            raise ValueError("Production topology requires a separate frontend; set CYBERLIFE_SERVE_FRONTEND=false")
        return self

    @property
    def origins(self) -> list[str]:
        return [x.strip().rstrip("/") for x in self.cors_origins.split(",") if x.strip()]

    @property
    def bootstrap_admin_uids(self) -> set[str]:
        return {x.strip() for x in self.admin_uids.split(",") if x.strip()}

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else (BASE_DIR / path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
