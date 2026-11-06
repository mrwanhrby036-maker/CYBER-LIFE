"""Identity verification: Firebase production; signed local sessions for development.

Local sessions are real password-authenticated sessions, not simulated Firebase
claims. They are disabled in production and cannot authorize Firebase storage.
"""
import hashlib
import hmac
import base64
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from app.errors import AuthenticationError, IntegrationError


@dataclass(frozen=True)
class Identity:
    uid: str
    email: str
    name: str
    provider: str
    email_verified: bool = False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str, salt: str | None = None, n: int = 16384) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt),
                            n=n, r=8, p=1, dklen=32)
    return f"scrypt${n}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        parts = encoded.split("$")
        if len(parts) == 4:
            algorithm, n, salt, expected = parts
            n = int(n)
        elif len(parts) == 3:
            algorithm, salt, expected = parts
            n = 16384
        else:
            return False
        if algorithm != "scrypt":
            return False
        actual = hash_password(password, salt, n).split("$")[3]
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


class LocalTokenService:
    def __init__(self, settings):
        self.secret = settings.local_secret
        if not self.secret:
            path = Path(settings.resolve(settings.data_dir)) / "local-signing-key"
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
                path.chmod(0o600)
            self.secret = path.read_text(encoding="utf-8").strip()
        if len(self.secret) < 32:
            raise ValueError("Local session secret must contain at least 32 characters")
        self.hours = settings.local_token_hours

    def issue(self, uid: str) -> tuple[str, int]:
        expires = int(time.time()) + self.hours * 3600
        payload = _b64(json.dumps({"sub": uid, "exp": expires,
                                   "iss": "cyberlife-local", "nonce": secrets.token_hex(8)}).encode())
        signature = _b64(hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).digest())
        return f"local.{payload}.{signature}", expires

    def verify(self, token: str) -> str:
        try:
            prefix, payload, signature = token.split(".")
            expected = _b64(hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).digest())
            if prefix != "local" or not hmac.compare_digest(signature, expected):
                raise AuthenticationError("جلسة غير صالحة")
            claims = json.loads(_unb64(payload))
            if claims["iss"] != "cyberlife-local" or claims["exp"] < time.time():
                raise AuthenticationError("انتهت الجلسة؛ سجّل الدخول مجدداً")
            return claims["sub"]
        except AuthenticationError:
            raise
        except Exception as exc:
            raise AuthenticationError("جلسة غير صالحة") from exc


class FirebaseAuthService:
    def __init__(self, repository):
        from firebase_admin import auth
        self.auth = auth
        self.app = repository.firebase_app

    async def verify(self, token: str) -> Identity:
        import asyncio
        try:
            claims = await asyncio.to_thread(self.auth.verify_id_token, token, self.app,
                                             check_revoked=True)
            return Identity(uid=claims["uid"], email=claims.get("email", ""),
                            name=claims.get("name", "متعلم"), provider="firebase",
                            email_verified=bool(claims.get("email_verified")))
        except Exception as exc:
            raise AuthenticationError("تعذر التحقق من هوية Firebase") from exc
