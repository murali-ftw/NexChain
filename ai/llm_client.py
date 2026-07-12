"""Gemini-only LLM client, shared by any P3 agent.

Provider-agnostic in shape (plain-text prompt in, plain-text answer
out — no reliance on structured output / function-calling), even
though there's currently a single provider behind it.

Configuration is read from the environment (see ai/.env.example):
    LLM_PRIMARY_PROVIDER / LLM_PRIMARY_MODEL / LLM_PRIMARY_API_KEY
No keys are hardcoded here. If a `.env` file exists at `ai/.env` it is
loaded automatically; real environment variables always take
precedence (python-dotenv does not override already-set variables).

There is no second-provider fallback: a failed call raises
LLMProviderError directly. This is a different layer from the
LangGraph per-node retry policy (`MAX_RETRIES_PER_NODE` in
ai/contracts.py, owned by the graph in P3.8) — do not conflate the two.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

DEFAULT_TIMEOUT_SECONDS = 20.0

_GEMINI_DEFAULT_MODEL = "gemini-flash-latest"


class LLMConfigError(RuntimeError):
    """Required LLM_PRIMARY_* configuration is missing or invalid."""


class LLMProviderError(RuntimeError):
    """The provider call failed (network error, timeout, non-2xx, bad response shape)."""


def _call_gemini(prompt: str, model: str, api_key: str, timeout: float) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    response = httpx.post(
        url,
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise LLMProviderError(f"Unexpected Gemini response shape: {data}") from exc


def _resolve_primary() -> tuple[str, str]:
    """Read `LLM_PRIMARY_MODEL` / `LLM_PRIMARY_API_KEY`. `LLM_PRIMARY_PROVIDER`
    must be "gemini" if set at all, kept only so ai/.env doesn't need to drop it."""
    provider = os.environ.get("LLM_PRIMARY_PROVIDER", "gemini").strip().lower()
    if provider != "gemini":
        raise LLMConfigError(
            f"Unsupported LLM_PRIMARY_PROVIDER '{provider}' — this client is Gemini-only"
        )
    model = os.environ.get("LLM_PRIMARY_MODEL", "").strip() or _GEMINI_DEFAULT_MODEL
    api_key = os.environ.get("LLM_PRIMARY_API_KEY", "").strip()
    if not api_key:
        raise LLMConfigError("LLM_PRIMARY_API_KEY is not set")
    return model, api_key


def generate(prompt: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    """Call Gemini and return its plain-text answer. Raises LLMConfigError if
    LLM_PRIMARY_* isn't configured, or LLMProviderError if the call fails."""
    model, api_key = _resolve_primary()
    try:
        return _call_gemini(prompt, model, api_key, timeout)
    except LLMProviderError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalize any failure into LLMProviderError
        raise LLMProviderError(f"Gemini call failed: {exc}") from exc
