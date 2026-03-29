"""Concrete LLM client implementations using httpx.

Supports Anthropic, OpenRouter, and DeepSeek providers.
All clients read API keys from environment variables by default.
Uses httpx.AsyncClient for async HTTP calls.
"""

from __future__ import annotations

import logging
import os
from itertools import cycle
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"

_OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
_DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class AnthropicClient:
    """Concrete LLM client implementation using the Anthropic Messages API.

    Satisfies the :class:`LLMClient` Protocol defined in stage_c.

    Args:
        model: Anthropic model identifier. Defaults to ``"claude-sonnet-4-20250514"``.
        max_tokens: Maximum number of tokens in the completion. Defaults to 4096.
        api_key: Anthropic API key. If not provided, reads from the
            ``ANTHROPIC_API_KEY`` environment variable.

    Raises:
        ValueError: If no API key is provided and ``ANTHROPIC_API_KEY`` is not set.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> None:
        """Initialise the client, resolving the API key from env if needed."""
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError("Anthropic API key not provided and ANTHROPIC_API_KEY environment variable is not set.")
        self._api_key: str = resolved_key
        self.model: str = model
        self.max_tokens: int = max_tokens

    async def complete(self, system: str, user: str) -> str:
        """Call the Anthropic Messages API and return the assistant text.

        Logs request metadata (model, token counts) but never logs prompt
        content or the API key.

        Args:
            system: System prompt string.
            user: User message string.

        Returns:
            The assistant's text response.

        Raises:
            ValueError: If the API returns a non-200 status code.
        """
        headers: dict[str, str] = {
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }

        logger.debug(
            "AnthropicClient.complete request: model=%s max_tokens=%d",
            self.model,
            self.max_tokens,
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)) as client:
            response = await client.post(
                _ANTHROPIC_API_URL,
                headers=headers,
                json=body,
            )

        if response.status_code != 200:
            raise ValueError(f"Anthropic API returned status {response.status_code}: {response.text[:500]}")

        data: dict[str, Any] = response.json()

        usage: dict[str, Any] = data.get("usage", {})
        logger.debug(
            "AnthropicClient.complete response: model=%s input_tokens=%s output_tokens=%s",
            data.get("model", self.model),
            usage.get("input_tokens"),
            usage.get("output_tokens"),
        )

        return str(data["content"][0]["text"])


class _OpenAICompatibleClient:
    """Base for OpenAI-compatible API clients (OpenRouter, DeepSeek).

    Subclasses provide :attr:`_api_url` and :attr:`_provider` as class-level
    constants and the ``__init__`` resolves the API key from the appropriate
    environment variable.

    Args:
        api_url: Full URL for the chat completions endpoint.
        env_var: Name of the environment variable holding the API key.
        default_model: Default model identifier used when none is specified.
        provider: Human-readable provider name for log messages.
        model: Model identifier. Falls back to ``default_model`` if not given.
        max_tokens: Maximum number of tokens in the completion. Defaults to 4096.
        api_key: API key. Reads from ``env_var`` if not provided.

    Raises:
        ValueError: If no API key is provided and ``env_var`` is not set.
    """

    def __init__(
        self,
        *,
        api_url: str,
        env_var: str,
        default_model: str,
        provider: str,
        model: str | None = None,
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> None:
        """Initialise the client, resolving the API key from env if needed."""
        resolved_key = api_key or os.environ.get(env_var)
        if not resolved_key:
            raise ValueError(f"{provider} API key not provided and {env_var} environment variable is not set.")
        self._api_key: str = resolved_key
        self._api_url: str = api_url
        self._provider: str = provider
        self.model: str = model if model is not None else default_model
        self.max_tokens: int = max_tokens

    async def complete(self, system: str, user: str) -> str:
        """Call the OpenAI-compatible API and return the assistant text.

        Logs request metadata (model, token counts) but never logs prompt
        content or the API key.

        Args:
            system: System prompt string.
            user: User message string.

        Returns:
            The assistant's text response.

        Raises:
            ValueError: If the API returns a non-200 status code.
        """
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        logger.debug(
            "%s.complete request: model=%s max_tokens=%d",
            self._provider,
            self.model,
            self.max_tokens,
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)) as client:
            response = await client.post(
                self._api_url,
                headers=headers,
                json=body,
            )

        if response.status_code != 200:
            raise ValueError(f"{self._provider} API returned status {response.status_code}: {response.text[:500]}")

        data: dict[str, Any] = response.json()

        usage: dict[str, Any] = data.get("usage", {})
        logger.debug(
            "%s.complete response: model=%s prompt_tokens=%s completion_tokens=%s",
            self._provider,
            data.get("model", self.model),
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )

        return str(data["choices"][0]["message"]["content"])


class OpenRouterClient(_OpenAICompatibleClient):
    """LLM client for the OpenRouter API (OpenAI-compatible format).

    Args:
        model: Model identifier. Defaults to ``"anthropic/claude-sonnet-4"``.
        max_tokens: Maximum number of tokens in the completion. Defaults to 4096.
        api_key: OpenRouter API key. If not provided, reads from the
            ``OPENROUTER_API_KEY`` environment variable.

    Raises:
        ValueError: If no API key is provided and ``OPENROUTER_API_KEY`` is not set.
    """

    def __init__(
        self,
        model: str = "anthropic/claude-sonnet-4",
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> None:
        """Initialise the OpenRouter client."""
        super().__init__(
            api_url=_OPENROUTER_API_URL,
            env_var="OPENROUTER_API_KEY",
            default_model="anthropic/claude-sonnet-4",
            provider="OpenRouterClient",
            model=model,
            max_tokens=max_tokens,
            api_key=api_key,
        )


class DeepSeekClient(_OpenAICompatibleClient):
    """LLM client for the DeepSeek API (OpenAI-compatible format).

    Args:
        model: Model identifier. Defaults to ``"deepseek-chat"``.
        max_tokens: Maximum number of tokens in the completion. Defaults to 4096.
        api_key: DeepSeek API key. If not provided, reads from the
            ``DEEPSEEK_API_KEY`` environment variable.

    Raises:
        ValueError: If no API key is provided and ``DEEPSEEK_API_KEY`` is not set.
    """

    def __init__(
        self,
        model: str = "deepseek-chat",
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> None:
        """Initialise the DeepSeek client."""
        super().__init__(
            api_url=_DEEPSEEK_API_URL,
            env_var="DEEPSEEK_API_KEY",
            default_model="deepseek-chat",
            provider="DeepSeekClient",
            model=model,
            max_tokens=max_tokens,
            api_key=api_key,
        )


class MockLLMClient:
    """Mock LLM client for testing. Returns pre-configured responses.

    Args:
        responses: A single string returned for every call, or a list of
            strings returned in order (cycling back to the start when exhausted).

    Attributes:
        calls: List of ``(system, user)`` tuples recorded for each invocation.
    """

    def __init__(self, responses: list[str] | str) -> None:
        """Initialise the mock with a fixed or cycling response set."""
        if isinstance(responses, str):
            self._cycle = cycle([responses])
        else:
            if not responses:
                raise ValueError("responses list must not be empty")
            self._cycle = cycle(responses)
        self.calls: list[tuple[str, str]] = []

    async def complete(self, system: str, user: str) -> str:
        """Return the next pre-configured response and record the call.

        Args:
            system: System prompt (recorded but not used for response selection).
            user: User message (recorded but not used for response selection).

        Returns:
            The next pre-configured response string.
        """
        self.calls.append((system, user))
        return next(self._cycle)


def create_llm_client(
    provider: str = "anthropic",
    model: str | None = None,
    api_key: str | None = None,
    max_tokens: int = 4096,
) -> AnthropicClient | OpenRouterClient | DeepSeekClient:
    """Create an LLM client for the specified provider.

    Args:
        provider: One of ``"anthropic"``, ``"openrouter"``, or ``"deepseek"``.
        model: Model name. Uses the provider's default if ``None``.
        api_key: API key. Reads from the appropriate environment variable if ``None``.
        max_tokens: Maximum response tokens. Defaults to 4096.

    Returns:
        A configured client instance for the given provider.

    Raises:
        ValueError: If ``provider`` is not a known value.
    """
    kwargs: dict[str, Any] = {"max_tokens": max_tokens}
    if model is not None:
        kwargs["model"] = model
    if api_key is not None:
        kwargs["api_key"] = api_key

    if provider == "anthropic":
        return AnthropicClient(**kwargs)
    elif provider == "openrouter":
        return OpenRouterClient(**kwargs)
    elif provider == "deepseek":
        return DeepSeekClient(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider!r}. Expected one of: 'anthropic', 'openrouter', 'deepseek'.")
