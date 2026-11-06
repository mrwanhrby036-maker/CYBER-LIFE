"""Firebase REALTIME DATABASE REST adapter (not Firestore).

The Admin SDK supplies short-lived OAuth credentials. REST provides path reads,
multi-path updates, server push IDs and ETag compare-and-swap transactions.
Service-account material is never returned to clients or written to logs.
"""
import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any
from urllib.parse import quote
import httpx
from app.db_base import Repository
from app.errors import IntegrationError, ConflictError
from app.helpers import safe_path

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/firebase.database",
          "https://www.googleapis.com/auth/userinfo.email"]


class FirebaseRepository(Repository):
    def __init__(self, settings):
        import firebase_admin
        from firebase_admin import credentials
        from google.auth.transport.requests import Request
        try:
            if settings.firebase_credentials_json:
                info = json.loads(settings.firebase_credentials_json)
            else:
                with open(settings.firebase_credentials_file, encoding="utf-8") as stream:
                    info = json.load(stream)
            if info.get("project_id") != settings.firebase_project_id:
                raise ValueError("Service account belongs to a different Firebase project")
            self.credential = credentials.Certificate(info)
            try:
                self.firebase_app = firebase_admin.get_app("cyber-life")
            except ValueError:
                self.firebase_app = firebase_admin.initialize_app(
                    self.credential, {"projectId": settings.firebase_project_id,
                                      "databaseURL": settings.firebase_database_url},
                    name="cyber-life")
            self.google_credential = self.credential.get_credential()
            self.request_type = Request
            self.base = settings.firebase_database_url
            self.client = httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=6.0))
            self.token_lock = asyncio.Lock()
        except IntegrationError:
            raise
        except Exception as exc:
            logger.error("Firebase initialization failed: %s", type(exc).__name__)
            raise IntegrationError("إعداد Firebase غير مكتمل أو غير صالح") from exc

    async def _token(self) -> str:
        async with self.token_lock:
            def refresh() -> str:
                if not self.google_credential.valid:
                    self.google_credential.refresh(self.request_type())
                return self.google_credential.token
            try:
                return await asyncio.to_thread(refresh)
            except Exception as exc:
                raise IntegrationError("تعذر الحصول على تصريح قاعدة البيانات") from exc

    def _url(self, path: str) -> str:
        return f"{self.base}/{quote(safe_path(path), safe='/')}.json" if path else f"{self.base}/.json"

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {await self._token()}"
        try:
            response = await self.client.request(method, self._url(path), headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise IntegrationError("قاعدة البيانات غير متاحة مؤقتاً") from exc
        if response.status_code == 401:
            # A revoked/rotated credential must not be retried indefinitely.
            raise IntegrationError("انتهت صلاحية اعتماد قاعدة البيانات")
        if response.status_code >= 500:
            raise IntegrationError("خدمة قاعدة البيانات غير متاحة مؤقتاً")
        return response

    async def get(self, path: str, default: Any = None) -> Any:
        response = await self._request("GET", path)
        if response.status_code == 404:
            return default
        if response.status_code != 200:
            raise IntegrationError("تعذر قراءة البيانات المطلوبة")
        value = response.json()
        return default if value is None else value

    async def set(self, path: str, value: Any) -> None:
        response = await self._request("PUT", path, json=value)
        if response.status_code != 200:
            raise IntegrationError("تعذر حفظ البيانات")

    async def update(self, path: str, values: dict[str, Any]) -> None:
        for child in values:
            safe_path(child)
        response = await self._request("PATCH", path, json=values)
        if response.status_code != 200:
            raise IntegrationError("تعذر تحديث البيانات")

    async def delete(self, path: str) -> None:
        await self.set(path, None)

    async def push(self, path: str, value: dict[str, Any]) -> str:
        response = await self._request("POST", path, json=value)
        if response.status_code != 200:
            raise IntegrationError("تعذر إنشاء السجل")
        return response.json()["name"]

    async def transaction(self, path: str, updater: Callable) -> Any:
        for attempt in range(6):
            read = await self._request("GET", path, headers={"X-Firebase-ETag": "true"})
            if read.status_code not in (200, 404):
                raise IntegrationError("تعذر قراءة المعاملة")
            etag = read.headers.get("ETag")
            current = read.json() if read.status_code == 200 else None
            replacement = updater(current)
            write = await self._request("PUT", path, json=replacement,
                                        headers={"if-match": etag or "null_etag"})
            if write.status_code == 200:
                return replacement
            if write.status_code == 412:
                await asyncio.sleep(0.03 * (2 ** attempt))
                continue
            raise IntegrationError("تعذر إتمام المعاملة")
        raise ConflictError("تعارض في تحديث البيانات؛ أعد المحاولة")

    async def health(self) -> dict[str, str]:
        await self.get("platform_settings/schema_version")
        return {"status": "ok", "adapter": "firebase_rtdb"}

    async def close(self) -> None:
        await self.client.aclose()
