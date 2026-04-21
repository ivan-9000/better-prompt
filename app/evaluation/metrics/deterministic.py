"""
Better Prompt — deterministic evaluation metrics.
No LLM calls required. Fast, reliable, rule-based scoring.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class MetricResult:
    name:    str
    score:   float
    passed:  bool
    details: str


# ── Helper ────────────────────────────────────────────────────────────────────
def _extract_json(text: str) -> Optional[dict]:
    """Try to parse JSON from raw text or a markdown code block."""
    # Strategy 1: direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract from markdown code block
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    return None


# ── Metric 1: Exact Match ─────────────────────────────────────────────────────
def exact_match(
    output: str,
    expected: str,
    case_sensitive: bool = False,
) -> MetricResult:
    """
    Check whether the model output exactly matches the expected string.

    Best for:
        Classification tasks where the answer should always be
        one specific word or phrase (e.g. BILLING, POSITIVE, YES).

    Args:
        output:         The raw model output string.
        expected:       The expected correct answer.
        case_sensitive: Whether to compare with case sensitivity.

    Returns:
        MetricResult with score 1.0 (pass) or 0.0 (fail).
    """
    a = output.strip()
    b = expected.strip()
    if not case_sensitive:
        a = a.lower()
        b = b.lower()
    passed = a == b
    return MetricResult(
        name="exact_match",
        score=1.0 if passed else 0.0,
        passed=passed,
        details=(
            "Exact match."
            if passed
            else f"Expected: {expected!r} — Got: {output.strip()!r}"
        ),
    )


# ── Metric 2: JSON Validity ───────────────────────────────────────────────────
def json_validity(
    output: str,
    required_keys: Optional[list[str]] = None,
) -> MetricResult:
    """
    Check whether the model output is valid, parseable JSON.

    Optionally checks that all required keys are present.

    Best for:
        Tasks where the model must return structured data
        (e.g. data extraction, API response generation).

    Args:
        output:        The raw model output string.
        required_keys: Optional list of keys that must exist in the JSON.

    Returns:
        MetricResult with score between 0.0 and 1.0.
    """
    parsed = _extract_json(output)

    if parsed is None:
        return MetricResult(
            name="json_validity",
            score=0.0,
            passed=False,
            details="Output is not valid JSON.",
        )

    if required_keys:
        missing = [k for k in required_keys if k not in parsed]
        if missing:
            score = round(
                1 - len(missing) / len(required_keys), 3
            )
            return MetricResult(
                name="json_validity",
                score=score,
                passed=False,
                details=f"Valid JSON but missing keys: {missing}",
            )

    return MetricResult(
        name="json_validity",
        score=1.0,
        passed=True,
        details="Valid JSON with all required keys present.",
    )


# ── Metric 3: Keyword Presence ────────────────────────────────────────────────
def keyword_presence(
    output: str,
    keywords: list[str],
    require_all: bool = True,
) -> MetricResult:
    """
    Check whether specific keywords appear in the model output.

    Best for:
        Ensuring the model always mentions required terms,
        disclaimers, or concepts (e.g. legal warnings, key facts).

    Args:
        output:      The raw model output string.
        keywords:    List of keywords to look for (case-insensitive).
        require_all: If True, all keywords must be present to pass.
                     If False, at least one keyword suffices.

    Returns:
        MetricResult with score = found / total keywords.
    """
    if not keywords:
        return MetricResult(
            name="keyword_presence",
            score=1.0,
            passed=True,
            details="No keywords specified.",
        )

    output_lower = output.lower()
    found  = [k for k in keywords if k.lower() in output_lower]
    score  = len(found) / len(keywords)
    passed = (score == 1.0) if require_all else (score > 0)

    return MetricResult(
        name="keyword_presence",
        score=round(score, 3),
        passed=passed,
        details=(
            f"{len(found)}/{len(keywords)} keywords found: "
            f"{found if found else 'none'}. "
            f"Missing: {[k for k in keywords if k not in found]}"
        ),
    )


# ── Metric 4: Length Constraint ───────────────────────────────────────────────
def length_constraint(
    output: str,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> MetricResult:
    """
    Check whether the model output length is within specified bounds.

    Best for:
        Tasks with strict output length requirements
        (e.g. one-word answers, short summaries, tweet-length responses).

    Args:
        output:  The raw model output string.
        min_len: Minimum character count (inclusive). None = no minimum.
        max_len: Maximum character count (inclusive). None = no maximum.

    Returns:
        MetricResult with score 1.0 (pass) or 0.0 (fail).
    """
    n      = len(output.strip())
    issues = []

    if min_len is not None and n < min_len:
        issues.append(f"too short ({n} < {min_len} chars)")
    if max_len is not None and n > max_len:
        issues.append(f"too long ({n} > {max_len} chars)")

    passed = not issues

    return MetricResult(
        name="length_constraint",
        score=1.0 if passed else 0.0,
        passed=passed,
        details=(
            f"Length: {n} chars. "
            + (",
