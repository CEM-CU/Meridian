"""Shared LLM client. All LLM calls in the pipeline go through this.

Uses httpx.AsyncClient. Handles: API key from env, model selection,
retry with exponential backoff (max 2), timeout (30s), response parsing,
structured logging of token usage.
"""

# TODO: Implement after shared models are verified.
# Placeholder so imports don't break.


class LLMClient:
    """Async LLM client for structured JSON completions."""

    pass
