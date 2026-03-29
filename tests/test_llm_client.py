"""Tests for shared.llm_client.

Covers AnthropicClient, OpenRouterClient, DeepSeekClient, MockLLMClient, and
create_llm_client factory.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx
import pytest
import respx

from meridian.common.llm_client import (
    AnthropicClient,
    DeepSeekClient,
    MockLLMClient,
    OpenRouterClient,
    create_llm_client,
)


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Mirror of the LLMClient protocol from stage_c for isolated testing."""

    async def complete(self, system: str, user: str) -> str: ...


# ---------------------------------------------------------------------------
# MockLLMClient tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mock_returns_single_response() -> None:
    """MockLLMClient with a str always returns that same string."""
    client = MockLLMClient("hello")
    result = await client.complete("sys", "user msg")
    assert result == "hello"


@pytest.mark.asyncio
async def test_mock_returns_single_response_repeatedly() -> None:
    """MockLLMClient with a str cycles the same value on every call."""
    client = MockLLMClient("fixed")
    for _ in range(5):
        assert await client.complete("s", "u") == "fixed"


@pytest.mark.asyncio
async def test_mock_cycles_through_list() -> None:
    """MockLLMClient cycles through a list of responses in order."""
    client = MockLLMClient(["first", "second", "third"])
    assert await client.complete("s", "u") == "first"
    assert await client.complete("s", "u") == "second"
    assert await client.complete("s", "u") == "third"
    # Cycles back to start
    assert await client.complete("s", "u") == "first"


@pytest.mark.asyncio
async def test_mock_records_calls() -> None:
    """MockLLMClient records every (system, user) pair in self.calls."""
    client = MockLLMClient(["r1", "r2"])
    await client.complete("system-a", "user-a")
    await client.complete("system-b", "user-b")
    assert client.calls == [("system-a", "user-a"), ("system-b", "user-b")]


def test_mock_raises_on_empty_list() -> None:
    """MockLLMClient raises ValueError when given an empty list."""
    with pytest.raises(ValueError):
        MockLLMClient([])


# ---------------------------------------------------------------------------
# AnthropicClient construction tests
# ---------------------------------------------------------------------------


def test_anthropic_client_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient raises ValueError when no key is provided and env is unset."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicClient()


def test_anthropic_client_accepts_explicit_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient does not raise when api_key is passed explicitly."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = AnthropicClient(api_key="sk-ant-test-key")
    assert client.model == "claude-sonnet-4-20250514"
    assert client.max_tokens == 4096


def test_anthropic_client_reads_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient reads ANTHROPIC_API_KEY from the environment."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
    client = AnthropicClient()
    assert client.model == "claude-sonnet-4-20250514"


def test_anthropic_client_custom_model_and_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient stores custom model and max_tokens values."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")
    client = AnthropicClient(model="claude-haiku-4-5", max_tokens=1024)
    assert client.model == "claude-haiku-4-5"
    assert client.max_tokens == 1024


# ---------------------------------------------------------------------------
# AnthropicClient.complete — mocked HTTP tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_client_complete_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient.complete returns the text from a successful API response."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    mock_response = {
        "id": "msg_01",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-4-20250514",
        "content": [{"type": "text", "text": "Extracted requirements here."}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }
    respx.post("https://api.anthropic.com/v1/messages").mock(return_value=httpx.Response(200, json=mock_response))

    client = AnthropicClient()
    result = await client.complete("You are an assistant.", "List requirements.")
    assert result == "Extracted requirements here."


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_client_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient.complete raises ValueError on a non-200 API response."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(401, json={"error": {"message": "invalid api key"}})
    )

    client = AnthropicClient()
    with pytest.raises(ValueError, match="401"):
        await client.complete("sys", "user")


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_client_raises_on_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient.complete raises ValueError on a 500 server error."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    client = AnthropicClient()
    with pytest.raises(ValueError, match="500"):
        await client.complete("sys", "user")


# ---------------------------------------------------------------------------
# Protocol compliance (runtime_checkable)
# ---------------------------------------------------------------------------


def test_anthropic_client_satisfies_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnthropicClient is an instance of the LLMClient Protocol."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    client = AnthropicClient()
    assert isinstance(client, LLMClientProtocol)


def test_mock_client_satisfies_protocol() -> None:
    """MockLLMClient is an instance of the LLMClient Protocol."""
    client = MockLLMClient("response")
    assert isinstance(client, LLMClientProtocol)


# ---------------------------------------------------------------------------
# OpenRouterClient construction tests
# ---------------------------------------------------------------------------


def test_openrouter_client_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient raises ValueError when no key is provided and env is unset."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        OpenRouterClient()


def test_openrouter_client_accepts_explicit_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient does not raise when api_key is passed explicitly."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = OpenRouterClient(api_key="sk-or-test-key")
    assert client.model == "anthropic/claude-sonnet-4"
    assert client.max_tokens == 4096


def test_openrouter_client_reads_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient reads OPENROUTER_API_KEY from the environment."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-env-key")
    client = OpenRouterClient()
    assert client.model == "anthropic/claude-sonnet-4"


def test_openrouter_client_custom_model_and_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient stores custom model and max_tokens values."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-x")
    client = OpenRouterClient(model="openai/gpt-4o", max_tokens=1024)
    assert client.model == "openai/gpt-4o"
    assert client.max_tokens == 1024


def test_openrouter_client_satisfies_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient is an instance of the LLMClient Protocol."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    client = OpenRouterClient()
    assert isinstance(client, LLMClientProtocol)


# ---------------------------------------------------------------------------
# OpenRouterClient.complete — mocked HTTP tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_complete_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient.complete returns the text from a successful API response."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    mock_response = {
        "id": "chatcmpl-01",
        "object": "chat.completion",
        "model": "anthropic/claude-sonnet-4",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "OpenRouter response text."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 80, "completion_tokens": 30},
    }
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    client = OpenRouterClient()
    result = await client.complete("You are an assistant.", "Describe the role.")
    assert result == "OpenRouter response text."


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient.complete raises ValueError on a non-200 API response."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": {"message": "invalid api key"}})
    )

    client = OpenRouterClient()
    with pytest.raises(ValueError, match="401"):
        await client.complete("sys", "user")


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_raises_on_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouterClient.complete raises ValueError on a 500 server error."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    client = OpenRouterClient()
    with pytest.raises(ValueError, match="500"):
        await client.complete("sys", "user")


# ---------------------------------------------------------------------------
# DeepSeekClient construction tests
# ---------------------------------------------------------------------------


def test_deepseek_client_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient raises ValueError when no key is provided and env is unset."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient()


def test_deepseek_client_accepts_explicit_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient does not raise when api_key is passed explicitly."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = DeepSeekClient(api_key="sk-ds-test-key")
    assert client.model == "deepseek-chat"
    assert client.max_tokens == 4096


def test_deepseek_client_reads_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient reads DEEPSEEK_API_KEY from the environment."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-env-key")
    client = DeepSeekClient()
    assert client.model == "deepseek-chat"


def test_deepseek_client_custom_model_and_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient stores custom model and max_tokens values."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-x")
    client = DeepSeekClient(model="deepseek-reasoner", max_tokens=2048)
    assert client.model == "deepseek-reasoner"
    assert client.max_tokens == 2048


def test_deepseek_client_satisfies_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient is an instance of the LLMClient Protocol."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-test")
    client = DeepSeekClient()
    assert isinstance(client, LLMClientProtocol)


# ---------------------------------------------------------------------------
# DeepSeekClient.complete — mocked HTTP tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_deepseek_client_complete_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient.complete returns the text from a successful API response."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-test")

    mock_response = {
        "id": "chatcmpl-ds-01",
        "object": "chat.completion",
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "DeepSeek response text."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 60, "completion_tokens": 20},
    }
    respx.post("https://api.deepseek.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    client = DeepSeekClient()
    result = await client.complete("You are an assistant.", "Summarise the document.")
    assert result == "DeepSeek response text."


@pytest.mark.asyncio
@respx.mock
async def test_deepseek_client_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient.complete raises ValueError on a non-200 API response."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-test")

    respx.post("https://api.deepseek.com/v1/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": {"message": "invalid api key"}})
    )

    client = DeepSeekClient()
    with pytest.raises(ValueError, match="401"):
        await client.complete("sys", "user")


@pytest.mark.asyncio
@respx.mock
async def test_deepseek_client_raises_on_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekClient.complete raises ValueError on a 500 server error."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-test")

    respx.post("https://api.deepseek.com/v1/chat/completions").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    client = DeepSeekClient()
    with pytest.raises(ValueError, match="500"):
        await client.complete("sys", "user")


# ---------------------------------------------------------------------------
# create_llm_client factory tests
# ---------------------------------------------------------------------------


def test_create_llm_client_returns_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_llm_client returns AnthropicClient for provider='anthropic'."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    client = create_llm_client(provider="anthropic")
    assert isinstance(client, AnthropicClient)


def test_create_llm_client_returns_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_llm_client returns OpenRouterClient for provider='openrouter'."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    client = create_llm_client(provider="openrouter")
    assert isinstance(client, OpenRouterClient)


def test_create_llm_client_returns_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_llm_client returns DeepSeekClient for provider='deepseek'."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-test")
    client = create_llm_client(provider="deepseek")
    assert isinstance(client, DeepSeekClient)


def test_create_llm_client_raises_on_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_llm_client raises ValueError for an unrecognised provider name."""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm_client(provider="unknown_provider")


def test_create_llm_client_passes_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_llm_client forwards the model argument to the constructed client."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    client = create_llm_client(provider="anthropic", model="claude-haiku-4-5")
    assert isinstance(client, AnthropicClient)
    assert client.model == "claude-haiku-4-5"


def test_create_llm_client_passes_max_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_llm_client forwards the max_tokens argument to the constructed client."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-test")
    client = create_llm_client(provider="deepseek", max_tokens=512)
    assert isinstance(client, DeepSeekClient)
    assert client.max_tokens == 512


def test_create_llm_client_passes_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_llm_client forwards the api_key argument, overriding env vars."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = create_llm_client(provider="openrouter", api_key="sk-or-explicit")
    assert isinstance(client, OpenRouterClient)
