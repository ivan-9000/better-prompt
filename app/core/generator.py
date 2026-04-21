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
    ) -> list:
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
    ) -> dict:
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

    def _parse_variants(self, raw: str) -> list:
        """Try 3 strategies to extract a JSON array from LLM output."""
        try:
            d = json.loads(raw.strip())
            if isinstance(d, list) and len(d) >= 1:
                return d
        except json.JSONDecodeError:
            pass
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            try:
                d = json.loads(m.group(1).strip())
                if isinstance(d, list):
                    return d
            except json.JSONDecodeError:
                pass
        m = re.search(r"(\[\s*\{[\s\S]*\}\s*\])", raw)
        if m:
            try:
                d = json.loads(m.group(1))
                if isinstance(d, list):
                    return d
            except json.JSONDecodeError:
                pass
        return []

    def _fallback_variants(self, question: str) -> list:
        """Return 5 template-based variants when the LLM is unavailable."""
        q = question.strip()
        return [
            {
                "variant_name": "Beginner Friendly",
                "enhanced_prompt": (
                    f"I am completely new to this topic and have no prior "
                    f"experience. Please explain {q} in the simplest possible "
                    f"way using everyday language and real-world analogies. "
                    f"Assume I know nothing and start from the very beginning. "
                    f"Avoid technical jargon — if you must use a technical "
                    f"term, please define it clearly."
                ),
                "why_better": (
                    "Removes assumed knowledge and explicitly requests "
                    "plain language and analogies."
                ),
                "best_for": (
                    "Absolute beginners with no background in the subject."
                ),
                "tone": "Conversational",
            },
            {
                "variant_name": "Technical Deep-Dive",
                "enhanced_prompt": (
                    f"Provide a comprehensive technical explanation of {q}. "
                    f"Cover the underlying mechanisms, architecture, and core "
                    f"principles. Include best practices, edge cases, "
                    f"performance considerations, and current industry "
                    f"standards. Assume I have professional experience and "
                    f"can handle full technical depth."
                ),
                "why_better": (
                    "Signals expertise level and requests the depth a "
                    "professional actually needs."
                ),
                "best_for": (
                    "Experienced practitioners seeking rigorous, "
                    "complete knowledge."
                ),
                "tone": "Technical",
            },
            {
                "variant_name": "Step-by-Step Practical",
                "enhanced_prompt": (
                    f"Give me a clear, actionable, numbered step-by-step "
                    f"guide on {q}. For each step, tell me exactly what to "
                    f"do, what tools or resources I need, and what the "
                    f"expected result looks like. Also highlight the most "
                    f"common mistakes to avoid at each stage. I want to be "
                    f"able to start immediately after reading this."
                ),
                "why_better": (
                    "Turns abstract knowledge into concrete actions "
                    "with tools and success criteria."
                ),
                "best_for": (
                    "People who learn by doing and want "
                    "immediate, practical results."
                ),
                "tone": "Structured",
            },
            {
                "variant_name": "Conceptual Understanding",
                "enhanced_prompt": (
                    f"Help me build a deep, lasting conceptual understanding "
                    f"of {q}. Do not just tell me what it is — explain WHY "
                    f"it works this way, WHY it matters, and how it connects "
                    f"to related concepts I may already know. Use mental "
                    f"models, analogies, and real-world examples to make it "
                    f"intuitive. I want to truly understand this, not just "
                    f"memorise facts."
                ),
                "why_better": (
                    "Prioritises genuine understanding and transferable "
                    "mental models over surface facts."
                ),
                "best_for": (
                    "Curious learners who want knowledge that sticks "
                    "and applies to new situations."
                ),
                "tone": "Analytical",
            },
            {
                "variant_name": "Expert Comparison",
                "enhanced_prompt": (
                    f"Compare all major approaches, tools, frameworks, or "
                    f"options related to {q}. For each option cover: what it "
                    f"is, when to use it, key strengths, key limitations, and "
                    f"who it suits best. Present a structured comparison, "
                    f"then end with a clear opinionated recommendation for "
                    f"the most common scenarios."
                ),
                "why_better": (
                    "Enables informed decision-making by mapping all "
                    "options with honest tradeoffs."
                ),
                "best_for": (
                    "Anyone who needs to choose between tools or "
                    "approaches and wants a recommendation."
                ),
                "tone": "Comparative",
            },
        ]

    def _few_shot_examples(self, task: str, base: str) -> str:
        """Generate 2 input/output examples for few-shot prompting."""
        try:
            extra = {"api_key": self.api_key} if self.api_key else {}
            r = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate exactly 2 input/output examples "
                            "for the given task. Format strictly as:\n"
                            "Input: ...\nOutput: ...\n\n"
                            "Input: ...\nOutput: ..."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Task: {task}\nBase prompt: {base}",
                    },
                ],
                temperature=0.5,
                max_tokens=300,
                **extra,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"[generator] _few_shot_examples failed: {e}")
            return (
                "Input: example input 1\nOutput: example output 1\n\n"
                "Input: example input 2\nOutput: example output 2"
            )
