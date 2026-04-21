"""
Tests for app/core/runner.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.runner import (
    PROVIDER_MODELS,
    RunResult,
    _provider_from_model,
)


def test_run_result_defaults():
    r = RunResult()
    assert r.output == ""
    assert r.success is True
    assert r.error is None
    assert r.cost_usd == 0.0
    assert r.tokens_input == 0
    assert r.tokens_output == 0


def test_run_result_failure():
    r = RunResult(success=False, error="timeout")
    assert r.success is False
    assert r.error == "timeout"


def test_run_result_with_data():
    r = RunResult(
        output="Paris",
        tokens_input=10,
        tokens_output=5,
        cost_usd=0.000025,
        latency_ms=342.5,
        provider="openai",
        model="gpt-4o-mini",
    )
    assert r.output == "Paris"
    assert r.tokens_input == 10
    assert r.cost_usd == 0.000025
    assert r.provider == "openai"


def test_provider_openai():
    assert _provider_from_model("gpt-4o") == "openai"
    assert _provider_from_model("gpt-4o-mini") == "openai"
    assert _provider_from_model("gpt-3.5-turbo") == "openai"


def test_provider_anthropic():
    assert _provider_from_model("claude-3-5-sonnet-20241022") == "anthropic"
    assert _provider_from_model("claude-3-haiku-20240307") == "anthropic"


def test_provider_groq():
    assert _provider_from_model("groq/llama-3.3-70b-versatile") == "groq"
    assert _provider_from_model("groq/llama-3.1-8b-instant") == "groq"
    assert _provider_from_model("groq/mixtral-8x7b-32768") == "groq"


def test_provider_ollama():
    assert _provider_from_model("ollama/llama3") == "ollama"
    assert _provider_from_model("ollama/mistral") == "ollama"


def test_provider_models_has_five_keys():
    assert len(PROVIDER_MODELS) == 5
    expected = {"openai", "anthropic", "google", "groq", "ollama"}
    assert set(PROVIDER_MODELS.keys()) == expected


def test_provider_models_all_nonempty():
    for provider, models in PROVIDER_MODELS.items():
        assert len(models) > 0, f"{provider} has no models listed"
