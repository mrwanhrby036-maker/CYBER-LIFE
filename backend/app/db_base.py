"""Repository contract shared by Firebase RTDB and the explicit local adapter."""
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class Repository(ABC):
    @abstractmethod
    async def get(self, path: str, default: Any = None) -> Any: ...

    @abstractmethod
    async def set(self, path: str, value: Any) -> None: ...

    @abstractmethod
    async def update(self, path: str, values: dict[str, Any]) -> None: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...

    @abstractmethod
    async def push(self, path: str, value: dict[str, Any]) -> str: ...

    @abstractmethod
    async def transaction(self, path: str, updater: Callable[[Any], Any]) -> Any:
        """Atomic compare-and-swap. updater returns the complete replacement node."""

    @abstractmethod
    async def close(self) -> None: ...

    async def health(self) -> dict[str, str]:
        return {"status": "ok", "adapter": type(self).__name__}
