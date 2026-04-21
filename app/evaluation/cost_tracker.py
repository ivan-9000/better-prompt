"""
Better Prompt — cost tracker.
Tracks token usage and calculates API costs per model.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ── Pricing table ─────────────────────────────────────────────────────────────
# Prices in USD per 1,000,000 tokens (input, output)
PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o":                        (5.00,  15.00),
    "gpt-4o-mini":                   (0.15,   0.60),
    "gpt-3.5-turbo":                 (0.50,   1.50),
    # Anthropic
    "claude-3-5-sonnet-20241022":    (3.00,  15.00),
    "claude-3-haiku-20240307":       (0.25,   1.25),
    # Google
    "gemini/gemini-1.5-pro":         (1.25,   5.00),
    "gemini/gemini-1.5-flash":       (0.075,  0.30),
    # Groq — free tier
    "groq/llama-3.3-70b-versatile":  (0.00,   0.00),
    "groq/llama-3.1-8b-instant":     (0.00,   0.00),
    "groq/mixtral-8x7b-32768":       (0.00,   0.00),
    # Ollama — local, always free
    "ollama/llama3":                 (0.00,   0.00),
    "ollama/mistral":                (0.00,   0.00),
}


# ── Cost calculation ──────────────────────────────────────────────────────────
def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate the USD cost of a single model call.

    Args:
        model:         The model identifier string.
        input_tokens:  Number of input (prompt) tokens used.
        output_tokens: Number of output (completion) tokens used.

    Returns:
        Cost in USD as a float. Returns 0.0 for unknown models.
    """
    price_in, price_out = PRICING.get(model, (0.0, 0.0))
    return (
        input_tokens  * price_in
        + output_tokens * price_out
    ) / 1_000_000


# ── Internal run record ───────────────────────────────────────────────────────
@dataclass
class _Run:
    model:         str
    input_tokens:  int
    output_tokens: int
    cost_usd:      float


# ── Tracker class ─────────────────────────────────────────────────────────────
class CostTracker:
    """
    Accumulates cost and token data across multiple model calls.

    Usage:
        tracker = CostTracker()
        cost = tracker.add_run("gpt-4o", 500, 200)
        print(tracker.summary())
    """

    def __init__(self) -> None:
        self._runs: list[_Run] = []

    def add_run(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Record a model call and return its cost in USD.

        Args:
            model:         The model identifier string.
            input_tokens:  Number of input tokens used.
            output_tokens: Number of output tokens used.

        Returns:
            Cost of this specific run in USD.
        """
        cost = calculate_cost(model, input_tokens, output_tokens)
        self._runs.append(
            _Run(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
            )
        )
        return cost

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def total_cost(self) -> float:
        """Total USD cost across all recorded runs."""
        return sum(r.cost_usd for r in self._runs)

    @property
    def total_input_tokens(self) -> int:
        """Total input tokens across all recorded runs."""
        return sum(r.input_tokens for r in self._runs)

    @property
    def total_output_tokens(self) -> int:
        """Total output tokens across all recorded runs."""
        return sum(r.output_tokens for r in self._runs)

    @property
    def cost_by_model(self) -> dict[str, float]:
        """Total cost grouped by model name."""
        out: dict[str, float] = {}
        for r in self._runs:
            out[r.model] = out.get(r.model, 0.0) + r.cost_usd
        return out

    @property
    def runs_by_model(self) -> dict[str, int]:
        """Number of runs grouped by model name."""
        out: dict[str, int] = {}
        for r in self._runs:
            out[r.model] = out.get(r.model, 0) + 1
        return out

    # ── Summary ───────────────────────────────────────────────────────────────
    def summary(self) -> dict:
        """
        Return a complete cost summary dictionary.

        Returns:
