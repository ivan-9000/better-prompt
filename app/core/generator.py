"""
Better Prompt — generator engine.
Handles prompt enhancement, language detection, and translation.
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

    # ── Public: detect language ───────────────────────────────────────────────
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.

        Returns a plain English language name e.g.
        "Slovak", "Czech", "German", "English", "French".
        Falls back to "English" if detection fails.
        """
        try:
            extra = {"api_key": self.api_key} if self.api_key else {}
            r = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a language detection expert. "
                            "Identify the language of the given text. "
                            "Reply with ONLY the language name in English. "
                            "Examples: English, Slovak, Czech, German, "
                            "French, Spanish, Polish, Hungarian. "
                            "One word only. No punctuation."
                        ),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                temperature=0.0,
                max_tokens=10,
                **extra,
            )
            language = r.choices[0].message.content.strip()
            logger.info(f"[generator] detected language: {language}")
            return language
        except Exception as e:
            logger.warning(f"[generator] language detection failed: {e}")
            return "English"

    # ── Public: translate variants ────────────────────────────────────────────
    def translate_variants(
        self,
        variants: list,
        target_language: str,
    ) -> list:
        """
        Translate the enhanced_prompt field of each variant
        into the target language.

        All other fields (variant_name, why_better, best_for, tone)
        are also translated so the full card is in the user's language.

        Skips translation if target_language is English.
        """
        if target_language.lower() == "english":
            return variants

        translated = []
        for variant in variants:
            try:
                extra = {"api_key": self.api_key} if self.api_key else {}

                original = json.dumps(variant, ensure_ascii=False)

                r = litellm.completion(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are a professional translator. "
                                f"Translate all text values in the given "
                                f"JSON object into {target_language}. "
                                f"Keep all JSON keys in English exactly "
                                f"as they are. "
                                f"Translate only the values. "
                                f"Return ONLY valid JSON. No extra text."
                            ),
                        },
                        {
                            "role": "user",
                            "content": original,
                        },
                    ],
                    temperature=0.3,
                    max_tokens=800,
                    **extra,
                )

                raw = r.choices[0].message.content or ""
                parsed = self._parse_single_variant(raw)

                if parsed:
                    translated.append(parsed)
                    logger.info(
                        f"[generator] translated variant "
                        f"'{variant.get('variant_name')}' "
                        f"to {target_language}"
                    )
                else:
                    logger.warning(
                        f"[generator] translation parse failed "
                        f"for '{variant.get('variant_name')}' "
                        f"— keeping original"
                    )
                    translated.append(variant)

            except Exception as e:
                logger.warning(
                    f"[generator] translation failed for "
                    f"'{variant.get('variant_name')}': {e} "
                    f"— keeping original"
                )
                translated.append(variant)

        return translated

    # ── Public: enhance prompt ────────────────────────────────────────────────
    def enhance_prompt(
        self,
        user_question: str,
        context: str = "",
        goal: str = "",
    ) -> list:
        """
        Main entry point.

        1. Detect the language of the user question
        2. Generate 5 variants (always in English for best quality)
        3. Translate all variants back to the user's language
        4. Return the translated variants
        """
        # Step 1 — detect language
        language = self.detect_language(user_question)

        # Step 2 — generate variants in English
        meta = self._build_meta_prompt(user_question, context, goal)
        variants = self._call_llm_for_variants(meta)

        # Step 3 — translate back to user language
        variants = self.translate_variants(variants, language)

        return variants

    # ── Public: generate classical technique variants ─────────────────────────
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

    # ── Public: meta prompt suggestion ───────────────────────────────────────
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

    # ── Private: call LLM for variants ────────────────────────────────────────
    def _call_llm_for_variants(self, meta: str) -> list:
        """Call the LLM and return parsed variants or fallback."""
        try:
            extra = {"api_key": self.api_key} if self.api_key else {}
            r = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a world-class prompt engineer. "
                            "Transform rough questions into precise, "
                            "detailed, highly effective prompts. "
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
                    f"[generator] {len(variants)} variants generated"
                )
                return variants
            logger.warning("[generator] 0 variants parsed — using fallback")
        except Exception as e:
            logger.warning(f"[generator] LLM call failed: {e}")
        return self._fallback_variants("")

    # ── Private: build meta prompt ────────────────────────────────────────────
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
1. Beginner Friendly       — plain language, no assumed knowledge
2. Technical Deep-Dive     — precise, detailed, professional level
3. Step-by-Step Practical  — action-oriented, numbered steps, tools
4. Conceptual Understanding — focus on WHY not HOW, mental models
5. Expert Comparison       — compare options, tradeoffs, recommendation

Return ONLY a valid JSON array with exactly 5 objects.
Each object must have these exact keys:
  "variant_name"    : label matching the angle (string)
  "enhanced_prompt" : the full improved prompt, minimum 40 words (string)
  "why_better"      : one sentence explaining what this adds (string)
  "best_for"        : who benefits most (string)
  "tone"            : one word — Conversational/Technical/Structured/Analytical/Comparative

No intro text. No markdown fences. JSON array only."""

    # ── Private: parse variants array ─────────────────────────────────────────
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

    # ── Private: parse single variant object ──────────────────────────────────
    def _parse_single_variant(self, raw: str) -> Optional[dict]:
        """Extract a single JSON object from LLM translation output."""
        try:
            d = json.loads(raw.strip())
            if isinstance(d, dict):
                return d
        except json.JSONDecodeError:
            pass
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            try:
                d = json.loads(m.group(1).strip())
                if isinstance(d, dict):
                    return d
            except json.JSONDecodeError:
                pass
        m = re.search(r"(\{[\s\S]*\})", raw)
        if m:
            try:
                d = json.loads(m.group(1))
                if isinstance(d, dict):
                    return d
            except json.JSONDecodeError:
                pass
        return None

    # ── Private: fallback variants ────────────────────────────────────────────
    def _fallback_variants(self, question: str) -> list:
        """Return 5 template-based variants when the LLM is unavailable."""
        q = question.strip() if question.strip() else "this topic"
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
                "best_for": "Absolute beginners with no background.",
                "tone": "Conversational",
            },
            {
                "variant_name": "Technical Deep-Dive",
                "enhanced_prompt": (
                    f"Provide a comprehensive technical explanation of {q}. "
                    f"Cover the underlying mechanisms, architecture, and core "
                    f"principles. Include best practices, edge cases, "
                    f"performance considerations, and current industry "
                    f"standards. Assume I have professional experience."
                ),
                "why_better": (
                    "Signals expertise level and requests the depth "
                    "a professional actually needs."
                ),
                "best_for": "Experienced practitioners seeking complete knowledge.",
                "tone": "Technical",
            },
            {
                "variant_name": "Step-by-Step Practical",
                "enhanced_prompt": (
                    f"Give me a clear, actionable, numbered step-by-step "
                    f"guide on {q}. For each step tell me exactly what to do, "
                    f"what tools I need, and the expected result. "
                    f"Highlight the most common mistakes to avoid. "
                    f"I want to start immediately after reading this."
                ),
                "why_better": (
                    "Turns abstract knowledge into concrete actions "
                    "with tools and success criteria."
                ),
                "best_for": "People who learn by doing.",
                "tone": "Structured",
            },
            {
                "variant_name": "Conceptual Understanding",
                "enhanced_prompt": (
                    f"Help me build a deep conceptual understanding of {q}. "
                    f"Explain WHY it works this way, WHY it matters, and how "
                    f"it connects to related concepts I may already know. "
                    f"Use mental models and analogies. I want to truly "
                    f"understand this, not just memorise facts."
                ),
                "why_better": (
                    "Prioritises genuine understanding and transferable "
                    "mental models over surface facts."
                ),
                "best_for": "Curious learners who want lasting knowledge.",
                "tone": "Analytical",
            },
            {
                "variant_name": "Expert Comparison",
                "enhanced_prompt": (
                    f"Compare all major approaches, tools, or options "
                    f"related to {q}. For each option cover: what it is, "
                    f"when to use it, key strengths, key limitations, "
                    f"and who it suits best. End with a clear recommendation "
                    f"for the most common scenarios."
                ),
                "why_better": (
                    "Enables informed decision-making with honest tradeoffs."
                ),
                "best_for": "Anyone choosing between options.",
                "tone": "Comparative",
            },
        ]

    # ── Private: few shot examples ────────────────────────────────────────────
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
