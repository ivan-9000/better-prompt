# 🏗️ Better Prompt — Architecture

## Overview

Better Prompt is built as a single-page Streamlit application with a
clean separation between the UI layer, the core logic layer, and the
storage layer.

---

## Project Structure

    better-prompt/
    ├── app/
    │   ├── main.py                  ← Streamlit entry point
    │   ├── config.py                ← pydantic-settings configuration
    │   ├── core/
    │   │   ├── runner.py            ← LiteLLM multi-provider runner
    │   │   ├── generator.py         ← prompt enhancement engine
    │   │   └── versioning.py        ← prompt version control
    │   ├── evaluation/
    │   │   ├── cost_tracker.py      ← token cost calculator
    │   │   └── metrics/
    │   │       ├── deterministic.py ← exact match, json, keywords
    │   │       └── llm_judge.py     ← LLM-as-a-Judge evaluator
    │   ├── storage/
    │   │   ├── models.py            ← SQLAlchemy ORM + Pydantic schemas
    │   │   └── database.py          ← session management + CRUD
    │   └── ui/
    │       ├── components/
    │       │   └── metrics_chart.py ← Plotly chart helpers
    │       └── pages/
    │           ├── enhance.py       ← core Enhance page
    │           ├── evaluation.py    ← Evaluation Suite page
    │           └── history.py       ← Version History page
    ├── tests/
    ├── examples/
    └── docs/

---

## Layer Responsibilities

### UI Layer (app/ui/)

Streamlit pages and reusable components. Each page exposes a single
`render()` function called from `app/main.py`. Pages read shared API
settings from `st.session_state` (set in the sidebar).

### Core Layer (app/core/)

Pure Python logic with no Streamlit dependency. Can be tested and
used independently of the UI.

- **runner.py** — wraps LiteLLM with retry logic and returns a
  structured `RunResult` object for every call
- **generator.py** — builds meta-prompts, calls the LLM, parses the
  JSON response, and falls back to hardcoded templates on failure
- **versioning.py** — persists prompt versions to a local JSON file,
  generates unified diffs, and compares performance scores

### Evaluation Layer (app/evaluation/)

Metric functions that score LLM outputs. Each metric returns a
`MetricResult` with a score (0.0 to 1.0), a passed flag, and a
human-readable details string.

### Storage Layer (app/storage/)

SQLAlchemy ORM models backed by SQLite. The database stores prompt
runs and evaluation results for the History page.

---

## Data Flow — Enhance Feature

    1. User types a rough question in the text area
    2. User clicks "Enhance My Prompt"
    3. enhance.py reads api_key and model from st.session_state
    4. PromptGenerator.enhance_prompt() builds the meta-prompt
    5. LiteLLM routes the call to the selected provider
    6. The LLM returns a JSON array of 5 variant objects
    7. _parse_variants() extracts the JSON (3 fallback strategies)
    8. If parsing fails, _fallback_variants() returns 5 templates
    9. enhance.py renders 5 variant cards with Copy/ChatGPT/Claude buttons
    10. ChatGPT button opens chatgpt.com/?q=URL_ENCODED_PROMPT
    11. Claude button opens claude.ai/new?q=URL_ENCODED_PROMPT

---

## Data Flow — Evaluation Feature

    1. User uploads a JSON test dataset
    2. User enters a system prompt
    3. User clicks "Run Evaluation"
    4. For each test case:
       a. run_prompt_sync() calls the LLM
       b. Selected metrics are applied to the output
       c. Results are collected into a list of dicts
    5. Results are displayed as a dataframe
    6. Average scores are visualised as a bar chart

---

## Key Design Decisions

**BYOK (Bring Your Own Key)**
Users provide their own API keys via the sidebar. Better Prompt never
stores or transmits keys beyond the current session. This keeps
hosting costs at zero regardless of usage.

**Fallback variants**
If the LLM call fails or returns malformed JSON, the generator falls
back to 5 hardcoded template variants. The user always gets a result.

**LiteLLM as the routing layer**
Switching providers is a one-word change in the model string. This
makes multi-provider support trivial and future-proofs the codebase
against provider changes.

**SQLite for storage**
Zero configuration, single file, works everywhere. Can be swapped for
PostgreSQL by changing one environment variable (DATABASE_URL).

**Streamlit session state for shared settings**
The API key and model selector live in the sidebar and are stored in
`st.session_state` with keys `global_api_key` and `global_model`.
All pages read from these keys, so settings apply everywhere.
