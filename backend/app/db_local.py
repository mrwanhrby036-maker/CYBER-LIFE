"""Persistent development RTDB-shaped JSON store. NOT a production database.

All reads/writes hit the same path-based data model as Firebase. Atomic file
replacement prevents partial JSON files; a process lock protects transactions.
This adapter is rejected by Settings when CYBERLIFE_ENV=production.
"""
import asyncio
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any
from collections.abc import Callable
from app.db_base import Repository
from app.helpers import safe_path, new_id
from app.errors import NotFoundError


class LocalRepository(Repository):
    def __init__(self, directory: Path, fsync: bool = True):
        self.path = Path(directory) / "database.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.fsync = fsync
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict:
        with self.path.open(encoding="utf-8") as stream:
            return json.load(stream)

    def _write(self, data: dict) -> None:
        fd, temporary = tempfile.mkstemp(prefix=".db-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, separators=(",", ":"))
                stream.flush()
                if self.fsync:
                    os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _resolve(data: dict, path: str, create: bool = False) -> tuple[dict | None, str | None]:
        if not path:
            return data, None
        parts = path.split("/")
        node = data
        for part in parts[:-1]:
            if part not in node or node[part] is None:
                if not create:
                    return None, None
                node[part] = {}
            if not isinstance(node[part], dict):
                if not create:
                    return None, None
                node[part] = {}
            node = node[part]
        return node, parts[-1]

    def _get(self, path: str, default: Any = None) -> Any:
        with self.lock:
            parent, key = self._resolve(self._read(), safe_path(path) if path else "")
            if parent is None:
                return default
            if key is None:
                return parent
            return parent.get(key, default)

    def _set(self, path: str, value: Any) -> None:
        with self.lock:
            data = self._read()
            if not path:
                if not isinstance(value, dict):
                    raise ValueError("Root must be an object")
                self._write(value)
                return
            parent, key = self._resolve(data, safe_path(path), create=True)
            if value is None:
                parent.pop(key, None)
            else:
                parent[key] = value
            self._write(data)

    def _update(self, path: str, values: dict[str, Any]) -> None:
        with self.lock:
            data = self._read()
            base = safe_path(path) if path else ""
            for child, value in values.items():
                target = f"{base}/{child.strip('/')}" if base else child.strip("/")
                parent, key = self._resolve(data, safe_path(target), create=True)
                if value is None:
                    parent.pop(key, None)
                else:
                    parent[key] = value
            self._write(data)

    def _transaction(self, path: str, updater: Callable) -> Any:
        with self.lock:
            data = self._read()
            parent, key = self._resolve(data, safe_path(path) if path else "")
            if not path:
                current = data
            elif parent is None:
                current = None
            else:
                current = parent.get(key)
            replacement = updater(current)
            if not path:
                self._write(replacement)
            else:
                parent, key = self._resolve(data, safe_path(path), create=True)
                if replacement is None:
                    parent.pop(key, None)
                else:
                    parent[key] = replacement
                self._write(data)
            return replacement

    async def get(self, path: str, default: Any = None) -> Any:
        return await asyncio.to_thread(self._get, path, default)

    async def set(self, path: str, value: Any) -> None:
        await asyncio.to_thread(self._set, path, value)

    async def update(self, path: str, values: dict[str, Any]) -> None:
        await asyncio.to_thread(self._update, path, values)

    async def delete(self, path: str) -> None:
        await self.set(path, None)

    async def push(self, path: str, value: dict[str, Any]) -> str:
        key = new_id("rec")
        await self.set(f"{path}/{key}", value)
        return key

    async def transaction(self, path: str, updater: Callable) -> Any:
        return await asyncio.to_thread(self._transaction, path, updater)

    async def close(self) -> None:
        return None
