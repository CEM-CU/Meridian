"""Shared protocols for Stage C modules."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Protocol defining the async LLM client interface.

    Any object with a matching ``complete`` method satisfies this protocol.
    Used by C1 (JD extraction) and C3 (CV assessment).
    """

    async def complete(
        self,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> str: ...
