"""
Better Prompt — Evaluation Suite page.
Run batch evaluations against test datasets and visualise results.
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.core.runner import run_prompt_sync
from app.evaluation.metrics.deterministic import (
    exact_match,
    json_validity,
    keyword_presence,
)
from app.evaluation.metrics.llm_judge import LLMJudge
from app.ui.components.metrics_chart import bar_chart_scores


def render() -> None:

    # ── Page header ───────────────────────────────────────────────────────────
    st.title("🧪 Evaluation Suite")
    st.markdown(
        "Upload a test dataset, enter a system prompt, and measure "
        "quality across multiple metrics automatically."
    )
    st.divider()

    # ── Sidebar config ────────────────────────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.subheader("⚙️ Evaluation Settings")

        eval_model = st.selectbox(
            "Model to evaluate",
            options=[
                "groq/llama-3.3-70b-versatile",
                "groq/llama-3.1-8b-instant",
                "gpt-4o-mini",
                "gpt-4o",
            ],
            key="eval_model",
        )

        eval_api_key = st.session_state.get("global_api_key", "")

        st.markdown("**Metrics to run:**")
        use_exact   = st.checkbox("Exact Match",       value=True)
        use_json    = st.checkbox("JSON Validity",      value=False)
        use_kw      = st.checkbox("Keyword Presence",   value=True)
        use_judge   = st.checkbox("LLM Judge",          value=False)

        judge_criteria = []
        if use_judge:
            judge_criteria = st.multiselect(
                "Judge criteria",
                options=[
                    "factuality",
                    "relevance",
                    "coherence",
                    "format_compliance",
                    "safety",
                    "completeness",
                ],
                default=["relevance", "coherence"],
            )

    # ── Step 1: Upload dataset ────────────────────────────────────────────────
    st.subheader("1 · Upload Test Dataset")
    st.markdown(
        "Upload a JSON file containing an array of test cases. "
        "Each test case must have an `input` field. "
        "Optional fields: `expected_output`, `keywords`."
    )

    uploaded = st.file_uploader(
        "Choose a JSON file",
        type=["json"],
        help="Array of objects with input / expected_output / keywords",
    )

    test_cases = []
    if uploaded:
        try:
            test_cases = json.load(uploaded)
            st.success(f"✅  Loaded {len(test_cases)} test cases.")
            with st.expander("Preview first 3 test cases"):
                st.json(test_cases[:3])
        except Exception as e:
            st.error(f"❌  Could not parse JSON: {e}")
            return

    # ── Step 2: System prompt ─────────────────────────────────────────────────
    st.divider()
    st.subheader("2 · System Prompt")
    system_prompt = st.text_area(
        label="Enter the system prompt you want to evaluate",
        height=160,
        placeholder=(
            "e.g.  You are a customer support specialist. "
            "Classify the complaint into: BILLING, TECHNICAL, "
            "GENERAL, REFUND, ACCOUNT. "
            "Reply with only the category name in uppercase."
        ),
    )

    # ── Step 3: Run ───────────────────────────────────────────────────────────
    st.divider()
    run_clicked = st.button(
        "🚀  Run Evaluation",
        type="primary",
        use_container_width=True,
    )

    if not run_clicked:
        return

    # ── Validation ────────────────────────────────────────────────────────────
    if not test_cases:
        st.warning("⚠️  Please upload a test dataset first.")
        return
    if not system_prompt.strip():
        st.warning("⚠️  Please enter a system prompt.")
        return

    # ── Run evaluation loop ───────────────────────────────────────────────────
    st.divider()
    st.subheader("3 · Results")

    results      = []
    progress_bar = st.progress(0, text="Running evaluation…")
    total        = len(test_cases)

    for idx, case in enumerate(test_cases):
        user_input      = case.get("input", "")
        expected_output = case.get("expected_output", "")
        keywords        = case.get("keywords", [])

        # Call the model
        run = run_prompt_sync(
            model=eval_model,
            prompt=system_prompt.strip(),
            user_input=user_input,
            api_key=eval_api_key if eval_api_key else None,
        )

        row: dict = {
            "input":    user_input[:60] + "…" if len(user_input) > 60 else user_input,
            "output":   run.output[:80] + "…" if len(run.output) > 80 else run.output,
            "latency":  f"{run.latency_ms:.0f} ms",
            "cost":     f"${run.cost_usd:.6f}",
            "success":  run.success,
        }

        # Exact match
        if use_exact and expected_output:
            em = exact_match(run.output, expected_output)
            row["exact_match"] = em.score

        # JSON validity
        if use_json:
            jv = json_validity(run.output)
            row["json_valid"] = jv.score

        # Keyword presence
        if use_kw and keywords:
            kp = keyword_presence(run.output, keywords)
            row["keyword_score"] = kp.score

        # LLM judge
        if use_judge and judge_criteria:
            judge  = LLMJudge(
                judge_model=eval_model,
                api_key=eval_api_key if eval_api_key else None,
            )
            _, avg = judge.judge_output(
                output=run.output,
                user_input=user_input,
                criteria=judge_criteria,
            )
            row["judge_score"] = round(avg / 10, 2)

        results.append(row)
        progress_bar.progress(
            (idx + 1) / total,
            text=f"Running evaluation… {idx + 1}/{total}",
        )

    progress_bar.empty()

    # ── Results table ─────────────────────────────────────────────────────────
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)

    # ── Metric summary ────────────────────────────────────────────────────────
    metric_cols = [
        c for c in ["exact_match", "json_valid", "keyword_score", "judge_score"]
        if c in df.columns
    ]

    if metric_cols:
        st.divider()
        st.subheader("4 · Score Summary")

