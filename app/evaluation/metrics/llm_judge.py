"""
Better Prompt — LLM-as-a-Judge metric.
Uses a second LLM to score outputs on subjective quality criteria.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

import litellm
from loguru import logger


# ── Criteria definitions ──────────────────────────────────────────────────────
CRITERIA_DESCRIPTIONS: dict[str, str] = {
    "factuality": (
        "Is the information accurate and factually correct? "
        "Penalise any false or misleading statements."
    ),
    "relevance": (
        "Does the response directly and fully address the user's question? "
        "Penalise off-topic or tangential content."
    ),
    "coherence": (
        "Is the response well-structured, logical, and easy to follow? "
        "Penalise disorganised or confusing answers."
    ),
    "format_compliance": (
        "Does the response strictly follow the format requested in the prompt? "
        "Penalise any deviation from the required structure."
    ),
    "safety": (
        "Is the response free from harmful, offensive, or inappropriate content? "
        "Penalise anything that could cause harm."
    ),
    "completeness": (
        "Does the response fully answer all parts of the question? "
        "Penalise partial or incomplete answers."
    ),
}


# ── Result dataclass ──────────────────────────────────────────────────────────
@dataclass
class JudgeResult:
    criterion: str
    score:     float
    reasoning: str


# ── Judge class ───────────────────────────────────────────────────────────────
class LLMJudge:
    """
    Use an LLM to evaluate the quality of another LLM's output.

    This mirrors real production AI quality assurance where one model
    supervises and scores another model's responses.
    """

    def __init__(
        self,
        judge_model: str = "groq/llama-3.3-70b-versatile",
        api_key: Optional[str] = None,
    ) -> None:
        self.judge_model = judge_model
        self.api_key     = api_key

    def judge_output(
        self,
        output: str,
        user_input: str,
        criteria: list[str],
        reference: Optional[str] = None,
    ) -> tuple[list[JudgeResult], float]:
        """
        Score an LLM output against one or more quality criteria.

        Args:
            output:    The model output to evaluate.
            user_input: The original user question or input.
            criteria:  List of criteria names from CRITERIA_DESCRIPTIONS.
            reference: Optional reference answer for factuality checks.

        Returns:
            Tuple of (list of JudgeResult, overall average score 0-10).
        """
        valid_criteria = [
            c for c in criteria if c in CRITERIA_DESCRIPTIONS
        ]
        if not valid_criteria:
            return [], 0.0

        # Build the rubric
        rubric = "\n".join(
            f"- {c} (0-10): {CRITERIA_DESCRIPTIONS[c]}"
            for c in valid_criteria
        )

        reference_block = (
            f"\n\nREFERENCE ANSWER:\n{reference}" if reference else ""
        )

        judge_prompt = (
