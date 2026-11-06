"""Small shared primitives with explicit validation and UTC timestamps."""
import hashlib
import hmac
import re
import secrets
import unicodedata
from datetime import datetime, timezone
from typing import Any
from app.errors import ValidationError

_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(12)}"


def safe_key(value: str) -> str:
    if not isinstance(value, str) or not _KEY.fullmatch(value):
        raise ValidationError("معرّف غير صالح")
    return value


def safe_path(path: str) -> str:
    parts = path.strip("/").split("/")
    if not path or any(not p or p in {".", "..", "$", "#", "[", "]"} for p in parts):
        raise ValidationError("مسار قاعدة البيانات غير صالح")
    return "/".join(parts)


def normalize_answer(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    value = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", value)
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}))
    value = re.sub(r"[^\w\u0600-\u06FF]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def text_fingerprint(value: str) -> str:
    return hashlib.sha256(normalize_answer(value).encode()).hexdigest()


def constant_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode(), right.encode())


def paginate(items: list, offset: int = 0, limit: int = 50) -> dict[str, Any]:
    return {"items": items[offset:offset + limit], "total": len(items),
            "offset": offset, "limit": limit,
            "has_more": offset + limit < len(items)}


def public_dict(value: dict, fields: set[str]) -> dict:
    return {k: v for k, v in value.items() if k in fields}
