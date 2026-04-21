"""
Better Prompt — LiteLLM runner.
Handles all AI model calls across providers with retry logic.
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional

import litellm
from loguru import logger
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
    ],
    "anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-haiku-20240307",
    ],
    "google": [
        "gemini/gemini-1.5-pro",
        "gemini/gemini-1.5-flash",
    ],
    "groq": [
        "groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-8b-instant",
        "groq/mixtral-8x7b-32768",
    ],
    "ollama": [
        "ollama/llama3",
        "ollama/mistral",
    ],
}


class RunResult(BaseModel):
    output: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    provider: str = ""
    model: str = ""
    error: Optional[str] = None
    success: bool = True


def _provider_from_model(model: str) -> str:
    """Identify which provider owns a given model string."""
    for provider, models in PROVIDER_MODELS.items():
        if model in models:
            return provider
    if model.startswith("ollama/"):
        return "ollama"
    if model.startswith("groq/"):
        return "groq"
    if model.startswith("gemini/"):
        return "google"
    return "unknown"


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    reraise=True,
)
async def run_prompt(
    model: str,
    prompt: str,
    user_input: str,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> RunResult:
    """Call an LLM asynchronously and return a structured RunResult."""
    provider = _provider_from_model(model)
    t0 = time.perf_counter()
    try:
        extra = {"api_key": api_key} if api_key else {}
        r = await litellm.acompletion(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",   "content": user_input},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            **extra,
        )
        ms  = (time.perf_counter() - t0) * 1000
        out = r.choices[0].message.content or ""
        u   = r.usage or {}
        ti  = getattr(u, "prompt_tokens", 0)
        to  = getattr(u, "completion_tokens", 0)
        try:
            cost = litellm.completion_cost(completion_response=r)
        except Exception:
            cost = 0.0
        logger.info(f"[runner] OK {model} {ms:.0f}ms ${cost:.6f}")
        return RunResult(
            output=out,
            tokens_input=ti,
            tokens_output=to,
            cost_usd=cost,
            latency_ms=round(ms, 2),
            provider=provider,
            model=model,
        )
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        logger.error(f"[runner] ERR {model}: {e}")
        return RunResult(
            latency_ms=round(ms, 2),
            provider=provider,
            model=model,
            success=False,
            error=str(e),
        )


def run_prompt_sync(
    model: str,
    prompt: str,
    user_input: str,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> RunResult:
    """Synchronous wrapper around run_prompt, safe for Streamlit."""
    coro = run_prompt(
        model, prompt, user_input, api_key, temperature, max_tokens
    )
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
