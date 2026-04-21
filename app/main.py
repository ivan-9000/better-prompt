"""
Better Prompt — entry point.
Run with: streamlit run app/main.py
"""
import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Better Prompt",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        st.title("✨ Better Prompt")
        st.markdown("*Turn rough questions into perfect AI prompts.*")
        st.divider()

        page = st.radio(
            "Navigate",
            ["✨ Enhance", "🧪 Evaluate", "📜 History"],
            label_visibility="collapsed",
        )

        st.divider()

        st.subheader("🔑 API Settings")
        st.text_input(
            "API Key",
            type="password",
            help="Groq is free — no credit card needed. Get yours at console.groq.com",
            key="global_api_key",
        )
        st.selectbox(
            "Model",
            options=[
                "groq/llama-3.3-70b-versatile",
                "groq/llama-3.1-8b-instant",
                "gpt-4o-mini",
                "gpt-4o",
            ],
            key="global_model",
        )

        st.divider()
        st.caption("v0.1.0 · MIT License")

    if page == "✨ Enhance":
        from app.ui.pages.enhance import render
    elif page == "🧪 Evaluate":
        from app.ui.pages.evaluation import render
    else:
        from app.ui.pages.history import render

    render()


if __name__ == "__main__":
    main()
