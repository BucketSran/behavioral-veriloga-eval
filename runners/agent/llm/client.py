"""LLM client — unified interface for Anthropic Messages API and OpenAI Chat Completions.

Supports four provider modes:
  - anthropic (native):        provider="anthropic"
  - anthropic-compatible:      provider="anthropic-compatible"  (DashScope, self-hosted, proxies)
  - openai (native):           provider="openai"
  - openai-compatible:         provider="openai-compatible"     (Azure, vLLM, ollama, local)

Adds retry/backoff that the legacy ``runners/generate.py`` lacks. For the
DashScope/Bailian models (qwen, glm, kimi, minimax), use
``provider="anthropic-compatible"`` with
``base_url="https://coding.dashscope.aliyuncs.com/apps/anthropic"``.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Literal

from ..config import LLMConfig


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    finish_reason: str
    elapsed_ms: float


class LLMError(Exception):
    """Raised when the LLM API returns an error."""


def _resolve_api_key(config: LLMConfig) -> str:
    if config.api_key_env:
        env_name = config.api_key_env
    else:
        env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "anthropic-compatible": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "openai-compatible": "OPENAI_API_KEY",
        }
        env_name = env_map.get(config.provider, "")

    api_key = os.environ.get(env_name, "")
    if not api_key:
        raise LLMError(
            f"{env_name} environment variable is not set. "
            f"Set it via 'export {env_name}=<your-key>' or configure api_key_env."
        )
    return api_key


# ─── Retry helper ──────────────────────────────────────────────

def _retry_call(fn, max_attempts: int = 3, base_delay: float = 1.0):
    """Call *fn* with exponential-backoff retry (1s, 2s, ...)."""
    last_exc: LLMError | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            delay = base_delay * (2 ** (attempt - 1))
            time.sleep(delay)
        try:
            return fn()
        except LLMError as e:
            last_exc = e
    raise last_exc  # type: ignore[misc]


# ─── Anthropic (native + compatible) ─────────────────────────

def _call_anthropic(
    config: LLMConfig,
    system: str,
    user: str,
    temperature: float,
) -> LLMResponse:
    try:
        import anthropic
    except ImportError:
        raise LLMError("anthropic package not installed. Run: pip install anthropic")

    api_key = _resolve_api_key(config)
    kwargs = {"api_key": api_key, "timeout": float(config.timeout)}
    if config.base_url:
        kwargs["base_url"] = config.base_url

    client = anthropic.Anthropic(**kwargs)

    t0 = time.perf_counter()
    try:
        message = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=temperature,
            top_p=config.top_p,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.APIError as e:
        raise LLMError(f"Anthropic API error: {e}") from e
    elapsed = (time.perf_counter() - t0) * 1000

    # Collect text from TextBlock and ThinkingBlock content blocks.
    # Some providers (DeepSeek) return ThinkingBlock for chain-of-thought.
    text = ""
    thinking = ""
    for block in message.content:
        block_type = getattr(block, "type", "text")
        if block_type == "text" and hasattr(block, "text"):
            text += block.text
        elif block_type == "thinking" and hasattr(block, "thinking"):
            thinking += block.thinking

    if not text and thinking:
        text = f"[thinking: {thinking[:300]}...]"

    return LLMResponse(
        text=text,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        finish_reason=message.stop_reason or "unknown",
        elapsed_ms=elapsed,
    )


# ─── OpenAI (native + compatible) ────────────────────────────

def _call_openai(
    config: LLMConfig,
    system: str,
    user: str,
    temperature: float,
    use_responses_api: bool = False,
) -> LLMResponse:
    try:
        import openai
    except ImportError:
        raise LLMError("openai package not installed. Run: pip install openai")

    api_key = _resolve_api_key(config)
    kwargs = {"api_key": api_key, "timeout": float(config.timeout)}
    if config.base_url:
        kwargs["base_url"] = config.base_url

    client = openai.OpenAI(**kwargs)

    t0 = time.perf_counter()
    try:
        if use_responses_api and not config.base_url:
            response = client.responses.create(
                model=config.model,
                instructions=system,
                input=user,
                temperature=temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
            )
            text = response.output_text or ""
            usage = response.usage or openai.types.responses.ResponseUsage(
                input_tokens=0, output_tokens=0, total_tokens=0
            )
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            finish_reason = getattr(response, "status", "unknown")
        else:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            response = client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )
            text = response.choices[0].message.content or ""
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            finish_reason = response.choices[0].finish_reason or "unknown"
    except openai.APIError as e:
        raise LLMError(f"OpenAI API error: {e}") from e

    elapsed = (time.perf_counter() - t0) * 1000

    return LLMResponse(
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        finish_reason=finish_reason,
        elapsed_ms=elapsed,
    )


# ─── Public API ──────────────────────────────────────────────

def call_llm(
    config: LLMConfig,
    system: str,
    user: str,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    use_responses_api: bool = False,
) -> LLMResponse:
    """Call the LLM with system + user messages. Returns LLMResponse.

    Retries up to 3 times with exponential backoff on transient errors.
    """
    temp = temperature if temperature is not None else config.temperature
    # NOTE: max_tokens override is applied to a copy of config so per-call values win.
    if max_tokens is not None and max_tokens != config.max_tokens:
        import dataclasses
        config = dataclasses.replace(config, max_tokens=max_tokens)

    provider = config.provider

    def _do_call() -> LLMResponse:
        if provider in ("anthropic", "anthropic-compatible"):
            return _call_anthropic(config, system, user, temp)
        elif provider in ("openai", "openai-compatible"):
            return _call_openai(config, system, user, temp, use_responses_api)
        else:
            raise LLMError(f"Unknown provider: {provider}. "
                           f"Expected: anthropic, anthropic-compatible, openai, openai-compatible")

    return _retry_call(_do_call)
