"""
Better Prompt — generator engine.
Handles prompt enhancement and classical variant generation.
"""
from __future__ import annotations

import json
import re
from typing import Optional

import litellm
from loguru import logger


class PromptGenerator:
    """Transform rough user questions into powerful prompt variants."""

    def __init__(
        self,
        model: str = "groq/llama-3.3-70b-versatile",
        api_key: Optional[str] = None,
    ) -> None:
        self.model = model
        self.api_key = api_key

    def enhance_prompt(
        self,
        user_question: str,
        context: str = "",
        goal: str = "",
    ) -> list[dict]:
        """Return 5 enhanced prompt variants for a rough user question."""
        meta = self._build_meta_prompt(user_question, context, goal)
        try:
            extra = {"api_key": self.api_key} if self.api_key else {}
            r = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a world-class prompt engineer. "
                            "Transform rough questions into precise, detailed, "
                            "highly effective prompts. "
                            "Always return valid JSON only. "
                            "No text outside the JSON array."
                        ),
                    },
                    {"role": "user", "content": meta},
                ],
                temperature=0.8,
                max_tokens=2000,
                **extra,
            )
            raw = r.choices[0].message.content or ""
            variants = self._parse_variants(raw)
            if variants:
                logger.info(
                    f"[generator] enhance_prompt → {len(variants)} variants"
                )
                return variants
            logger.warning("[generator] 0 variants parsed — using fallback")
        except Exception as e:
            logger.warning(f"[generator] LLM call failed: {e}")
        return self._fallback_variants(user_question)

    def generate_variants(
        self,
        task_description: str,
        base_prompt: str,
    ) -> dict[str, str]:
        """Return 5 classical prompt engineering technique variants."""
        examples = self._few_shot_examples(task_description, base_prompt)
        return {
            "zero_shot": base_prompt.strip(),
            "chain_of_thought": (
                base_prompt.strip()
                + "\n\nThink step by step before giving your final answer."
            ),
            "role_based": (
                f"You are an expert in {task_description}.\n\n"
                + base_prompt.strip()
            ),
            "structured_output": (
                base_prompt.strip()
                + "\n\nRespond ONLY in valid JSON format. No extra text."
            ),
            "few_shot": (
                base_prompt.strip()
                + "\n\nExamples:\n"
                + examples
                + "\n\nNow complete:"
            ),
        }

    def generate_meta_prompt(self, task_description: str) -> str:
        """Ask the LLM to write an optimised system prompt for a task."""
        try:
            extra = {"api_key": self.api_key} if self.api_key else {}
            r = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert prompt engineer. "
                            "Write the best possible system prompt for the "
                            "given task. Return ONLY the prompt text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Task: {task_description}",
                    },
                ],
                temperature=0.7,
                max_tokens=400,
                **extra,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"[generator] generate_meta_prompt failed: {e}")
            return (
                f"You are a helpful expert assistant for: {task_description}"
            )

    def _build_meta_prompt(
        self, question: str, context: str, goal: str
    ) -> str:
        context_block = (
            f"\nUser background: {context}" if context else ""
        )
        goal_block = (
            f"\nUser goal: {goal}" if goal else ""
        )
        return f"""A user wants to ask an AI assistant the following rough question:

"{question}"{context_block}{goal_block}

Your task: generate exactly 5 enhanced versions of this question.
Each version must target a different angle, audience, or depth level.

Cover exactly these 5 angles in this order:
1. Beginner Friendly       — plain language, no assumed knowledge, analogies welcome
2. Technical Deep-Dive     — precise, detailed, assumes professional experience
3. Step-by-Step Practical  — action-oriented, numbered steps, tools listed
4. Conceptual Understanding — focus on WHY not HOW, build mental models
5. Expert Comparison       — compare options, weigh tradeoffs, end with recommendation

Return ONLY a valid JSON array with exactly 5 objects.
Each object must have these exact keys:
  "variant_name"    : label matching the angle (string)
  "enhanced_prompt" : the full improved prompt, minimum 40 words (string)
  "why_better"      : one sentence explaining what this adds (string)
  "best_for"        : who benefits most (string)
  "tone"            : one word — Conversational/Technical/Structured/Analytical/Comparative

No intro text. No markdown fences. JSON array only."""

    def _parse_variants(self, raw: str) -> list[dict]:
        """Try 3 strategies to extract a JSON array from LLM output."""
        try:
            d = json.loads(raw.strip())
