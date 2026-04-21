# ✨ Better Prompt

> **Turn rough questions into perfect AI prompts — instantly.**

Better Prompt is an open-source AI prompt enhancement tool. Type a rough question, get 5 powerful variants back — each targeting a different angle, audience, or depth level. Open any variant directly in ChatGPT or Claude with one click.

---

## ✨ Features

- 🚀 **Instant Enhancement** — turn a vague question into 5 precise, powerful prompts in seconds
- 🎯 **5 Unique Angles** — Beginner Friendly, Technical Deep-Dive, Step-by-Step Practical, Conceptual Understanding, Expert Comparison
- 💬 **One-Click Launch** — open any variant directly in ChatGPT or Claude with the prompt pre-filled
- 🧪 **Evaluation Suite** — batch-test prompts against datasets using Exact Match, JSON Validity, Keyword Presence, and LLM Judge
- 📜 **Version History** — save, compare, and diff prompt versions over time like Git for prompts
- 🔌 **Multi-Provider** — supports Groq (free), OpenAI, Anthropic, Google, and Ollama

---

## 🏗️ Architecture

    User
     │
     ▼
    Streamlit UI  (app/main.py)
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
     │        ├── 💬 Open in ChatGPT  (chatgpt.com/?q=...)
     │        └── 🤖 Open in Claude   (claude.ai/new?q=...)
     │
     ├── 🧪 Evaluate Page
     │        │
     │        ▼
     │    run_prompt_sync → Metrics → Results Table → Bar Chart
     │
     └── 📜 History Page
              │
              ▼
          VersionControl → Diff Viewer → Performance Comparison

---

## ⚡ Quickstart

**1. Clone the repo**

    git clone https://github.com/yourusername/better-prompt.git
    cd better-prompt

**2. Create a virtual environment**

    python -m venv .venv

    # Windows
    .venv\Scripts\activate

    # Mac / Linux
    source .venv/bin/activate

**3. Install dependencies**

    pip install -r requirements.txt

**4. Add your API key**

    cp .env.example .env

Open `.env` and add your free Groq key from https://console.groq.com

    GROQ_API_KEY=gsk_your_key_here

**5. Run the app**

    streamlit run app/main.py

Open your browser at **http://localhost:8501** and start enhancing prompts.

---

## ☁️ Deploy to Streamlit Cloud (free)

1. Push this repo to GitHub
2. Go to https://share.streamlit.io
3. Click **New app** and select your repo
4. Set main file path to `app/main.py`
5. Click **Advanced settings** and add your secret:

       GROQ_API_KEY = "gsk_your_key_here"

6. Click **Deploy** — your app will be live in about 2 minutes

---

## 🛠️ Tech Stack

| Technology | Role | Why |
|---|---|---|
| Python 3.11 | Core language | AI ecosystem standard |
| Streamlit | UI framework | Fastest path to interactive web app |
| LiteLLM | LLM router | One interface for all providers |
| Groq | Default LLM provider | Free, extremely fast |
| Pydantic | Data validation | Catches errors before they crash |
| SQLAlchemy | ORM | Database without raw SQL |
| SQLite | Database | Zero config, file-based storage |
| Plotly | Charts | Interactive, beautiful, free |
| Tenacity | Retry logic | Resilient API calls |
| Loguru | Logging | Clear, structured logs |

---

## 🗺️ Roadmap

- [x] Prompt Enhancer with 5 variants
- [x] ChatGPT and Claude one-click buttons
- [x] Optional context and goal selectors
- [x] Evaluation Suite with 4 metrics
- [x] Version History with diff viewer
- [ ] Share button — shareable link to a variant
- [ ] Demo mode — no API key required
- [ ] Prompt categories — Coding, Writing, Learning, Business
- [ ] Export results to CSV
- [ ] Team mode — shared prompt library

---

## 🤝 Contributing

Contributions are welcome. Please read `docs/CONTRIBUTING.md` before opening a pull request.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using Python, Streamlit, and LiteLLM.*
