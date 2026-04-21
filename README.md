# ✨ Better Prompt

> **Turn rough questions into perfect AI prompts — instantly.**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

Better Prompt is an open-source AI prompt enhancement tool.
Type a rough question, get 5 powerful variants back — each
targeting a different angle, audience, or depth level.
Open any variant directly in ChatGPT or Claude with one click.

---

## ✨ Features

- 🚀 **Instant Enhancement** — turn a vague question into 5 precise,
  powerful prompts in seconds
- 🎯 **5 Unique Angles** — Beginner Friendly, Technical Deep-Dive,
  Step-by-Step, Conceptual, Expert Comparison
- 💬 **One-Click Launch** — open any variant directly in ChatGPT or
  Claude with the prompt pre-filled
- 🧪 **Evaluation Suite** — batch-test prompts against datasets using
  Exact Match, JSON Validity, Keyword Presence, and LLM Judge metrics
- 📜 **Version History** — save, compare, and diff prompt versions over
  time like Git for prompts
- 🔌 **Multi-Provider** — supports Groq (free), OpenAI, Anthropic,
  Google, and Ollama

---

## 🏗️ Architecture

    User
     │
     ▼
    Streamlit UI (app/main.py)
     │
     ├── ✨ Enhance Page
     │        │
     │        ▼
     │    PromptGenerator
     │        │
     │        ▼
     │    LiteLLM ──────────► Groq / OpenAI / Claude / Gemini
     │        │
     │        ▼
     │    5 Variant Cards
     │        ├── 💬 Open in ChatGPT
     │        └── 🤖 Open in Claude
     │
     ├── 🧪 Evaluate Page
     │        │
     │        ▼
     │    run_prompt_sync → Metrics → Results → Chart
     │
     └── 📜 History Page
              │
              ▼
          VersionControl → Diff Viewer → Comparison
