"""
Better Prompt — Enhance page.
Core feature: turn rough questions into 5 powerful prompt variants
with one-click buttons to open them in ChatGPT or Claude.
"""
from __future__ import annotations

import urllib.parse

import streamlit as st

from app.core.generator import PromptGenerator

CARD_EMOJIS = ["🟢", "🔵", "🟡", "🟠", "🔴"]


def render() -> None:

    # ── Global font size override ─────────────────────────────────────────────
    st.markdown(
        """
        <style>
        .main p, .main li, .main label {
            font-size: 1.05rem;
            line-height: 1.7;
        }
        .main h3 {
            font-size: 1.1rem;
            margin-bottom: 4px;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label {
            font-size: 0.95rem;
        }
        @media (max-width: 768px) {
            .main p, .main li {
                font-size: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Page header ───────────────────────────────────────────────────────────
    st.title("✨ Better Prompt")
    st.markdown(
        "Type your rough question below. "
        "We will turn it into **5 powerful prompt variants** — "
        "each ready to use in ChatGPT, Claude, or any AI assistant."
    )
    st.divider()

    # ── Session state init ────────────────────────────────────────────────────
    if "session_count" not in st.session_state:
        st.session_state["session_count"] = 0
    if "copied_index" not in st.session_state:
        st.session_state["copied_index"] = None

    # ── Sidebar extras ────────────────────────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.subheader("💡 Tips")
        st.markdown(
            """
- Be specific about your topic
- Fill in the optional fields for better results
- Each variant suits a **different goal** — try a few
- Click **Open in ChatGPT** or **Open in Claude**
  to jump straight to the answer
            """
        )
        st.divider()
        st.subheader("📊 Session Stats")
        st.metric(
            label="Prompts Enhanced This Session",
            value=st.session_state["session_count"],
        )

    # ── Main input ────────────────────────────────────────────────────────────
    user_question = st.text_area(
        label="Your question or idea",
        height=120,
        placeholder=(
            "e.g.  how to build a website  ·  explain machine learning  "
            "·  help me write an email to my boss  ·  what is blockchain  "
            "·  how does the stock market work"
        ),
    )

    # ── Optional context and goal ─────────────────────────────────────────────
    context = ""
    goal    = ""
    with st.expander("⚙️  Optional: Tell us about yourself  (improves results)"):
        st.markdown(
            "Filling these in helps us tailor each variant to your "
            "background and what you actually want to achieve."
        )
        context = st.selectbox(
            label="I am a…",
            options=[
                "",
                "Complete beginner",
                "Student",
                "Professional (non-technical)",
                "Developer / Engineer",
                "Researcher",
                "Business owner",
            ],
            help="Sets the assumed knowledge level across all 5 variants.",
        )
        goal = st.selectbox(
            label="I want to…",
            options=[
                "",
                "Get a quick answer",
                "Learn and understand deeply",
                "Get step-by-step instructions",
                "Compare options and make a decision",
                "Get code or a technical implementation",
                "Get a professional document or template",
            ],
            help="Focuses the variants on your intended outcome.",
        )

    st.divider()

    # ── Enhance button ────────────────────────────────────────────────────────
    enhance_clicked = st.button(
        label="✨  Enhance My Prompt",
        type="primary",
        use_container_width=True,
    )

    if not enhance_clicked:
        st.markdown(
            "<br>"
            "<p style='text-align:center; color:#888; font-size:1.05em;'>"
            "👆  Enter your question above and click "
            "<b>Enhance My Prompt</b>"
            "</p>",
            unsafe_allow_html=True,
        )
        return

    # ── Validation ────────────────────────────────────────────────────────────
    if not user_question.strip():
        st.warning("⚠️  Please enter a question or topic before enhancing.")
        return

    # ── Read API settings from shared session state ───────────────────────────
    api_key = st.session_state.get("global_api_key", "")
    model   = st.session_state.get(
        "global_model", "groq/llama-3.3-70b-versatile"
    )
    groq_models = {
        "groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-8b-instant",
    }

    if not api_key and model not in groq_models:
        st.warning(
            f"⚠️  **{model}** requires an API key. "
            "Please add your key in the sidebar, or switch to a free "
            "**Groq model** at https://console.groq.com."
        )
        return

    # ── Generate variants ─────────────────────────────────────────────────────
    with st.spinner("🔮  Crafting your 5 enhanced prompt variants…"):
        try:
            generator = PromptGenerator(
                model=model,
                api_key=api_key if api_key else None,
            )
            variants = generator.enhance_prompt(
                user_question=user_question.strip(),
                context=context,
                goal=goal,
            )
        except Exception as exc:
            st.error(f"❌  Something went wrong: {exc}")
            st.info(
                "💡  **Suggestions:**\n"
                "- Switch to **groq/llama-3.1-8b-instant** in the sidebar\n"
                "- Check that your API key is correct\n"
                "- Try a shorter or simpler question"
            )
            return

    # ── Update session state ──────────────────────────────────────────────────
    st.session_state["session_count"] += 1
    st.session_state["copied_index"]   = None

    # ── Results header ────────────────────────────────────────────────────────
    st.success(f"✅  Done! Generated {len(variants)} enhanced variants.")
    st.markdown(
        f"**Your original question:** *{user_question.strip()}*"
    )
    st.divider()
    st.subheader("Your 5 Enhanced Prompt Variants")
    st.markdown(
        "Each variant takes a different angle. "
        "Pick the one that matches your goal — "
        "then open it directly in ChatGPT or Claude with one click."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Variant cards ─────────────────────────────────────────────────────────
    for i, variant in enumerate(variants):
        emoji      = CARD_EMOJIS[i % len(CARD_EMOJIS)]
        name       = variant.get("variant_name",    f"Variant {i + 1}")
        prompt     = variant.get("enhanced_prompt", "")
        why_better = variant.get("why_better",      "")
        best_for   = variant.get("best_for",        "")
        tone       = variant.get("tone",            "")

        encoded     = urllib.parse.quote(prompt)
        chatgpt_url = f"https://chatgpt.com/?q={encoded}"
        claude_url  = f"https://claude.ai/new?q={encoded}"

        # ── Card using background colour instead of border ────────────────
        st.markdown(
            f"""
            <div style='
                background:#F5F3FF;
                border-radius:12px;
                padding:24px 24px 8px 24px;
                margin-bottom:16px;
            '>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;'>
                    <span style='font-size:1.2em; font-weight:700;'>{emoji}&nbsp;&nbsp;{name}</span>
                    <span style='
                        background:#EDE9FE;
                        color:#5B21B6;
                        padding:4px 12px;
                        border-radius:12px;
                        font-size:0.78em;
                        font-weight:600;
                    '>{tone}</span>
                </div>
                <p style='margin:6px 0 2px 0; font-size:0.95em;'>
                    <strong>Best for:</strong> {best_for}
                </p>
                <p style='margin:2px 0 12px 0; font-size:0.9em; font-style:italic; color:#555;'>
                    {why_better}
                </p>
                <div style='
                    background:#FFFFFF;
                    border-radius:8px;
                    padding:16px;
                    font-family:monospace;
                    font-size:0.9em;
                    line-height:1.6;
                    white-space:pre-wrap;
                    word-wrap:break-word;
                    color:#1F1F1F;
                    margin-bottom:16px;
                '>{prompt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Action buttons ────────────────────────────────────────────────
        btn_copy, btn_gpt, btn_claude = st.columns(3)

        with btn_copy:
            if st.button(
                "📋  Copy prompt",
                key=f"copy_{i}",
                use_container_width=True,
            ):
                st.session_state["copied_index"] = i

        with btn_gpt:
            st.link_button(
                "💬  Open in ChatGPT",
                url=chatgpt_url,
                use_container_width=True,
            )

        with btn_claude:
            st.link_button(
                "🤖  Open in Claude",
                url=claude_url,
                use_container_width=True,
            )

        # ── Copy popup — appears below when Copy is clicked ───────────────
        if st.session_state.get("copied_index") == i:
            st.markdown(
                """
                <div style='
                    background:#F0FDF4;
                    border:1px solid #86EFAC;
                    border-radius:10px;
                    padding:16px 20px;
                    margin-top:8px;
                '>
                    <p style='margin:0 0 8px 0; font-weight:700; color:#166534;'>
                        📋 How to copy this prompt
                    </p>
                    <ol style='margin:0; padding-left:20px; color:#166534; line-height:1.8;'>
                        <li>Click inside the text box below</li>
                        <li>Press <strong>Ctrl+A</strong> to select all</li>
                        <li>Press <strong>Ctrl+C</strong> to copy</li>
                        <li>Paste anywhere with <strong>Ctrl+V</strong></li>
                    </ol>
                    <p style='margin:8px 0 0 0; font-size:0.82em; color:#4ADE80;'>
                        💡 On Mac use Cmd instead of Ctrl
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.text_area(
                label="",
                value=prompt,
                height=100,
                key=f"copy_area_{i}",
                label_visibility="collapsed",
            )

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Bottom tip ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        "💡 **Pro tip:** Try the same question with a different "
        "*'I want to…'* option — you will get completely different "
        "variants. The **Expert Comparison** variant is especially "
        "useful when choosing between tools, frameworks, or approaches."
    )
