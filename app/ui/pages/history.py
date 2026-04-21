"""
Better Prompt — Version History page.
Browse saved prompt versions, view diffs, and compare performance.
"""
from __future__ import annotations

import streamlit as st

from app.core.versioning import VersionControl


def render() -> None:

    # ── Page header ───────────────────────────────────────────────────────────
    st.title("📜 Prompt Version History")
    st.markdown(
        "Browse all saved prompt versions, compare changes side by side, "
        "and track performance improvements over time."
    )
    st.divider()

    # ── Load version control ──────────────────────────────────────────────────
    vc    = VersionControl()
    names = vc.list_names()

    if not names:
        st.info(
            "💡  No prompt versions saved yet. "
            "Run an evaluation and save a version to get started."
        )
        st.divider()
        st.subheader("How to save a version")
        st.markdown(
            """
1. Go to the **🧪 Evaluate** page
2. Enter a system prompt and run an evaluation
3. Click **Save Version** to record it here
4. Repeat with an improved prompt to track progress
            """
        )
        return

    # ── Prompt selector ───────────────────────────────────────────────────────
    selected_name = st.selectbox(
        label="Select a prompt to inspect",
        options=names,
        help="Choose which prompt's history you want to view.",
    )

    history = vc.get_history(selected_name)
    st.markdown(
        f"**{len(history)} version(s)** found for "
        f"*{selected_name}*"
    )
    st.divider()

    # ── Version cards ─────────────────────────────────────────────────────────
    st.subheader("📋 All Versions")

    for version in reversed(history):
        score_badge = (
            f"🟢 Score: {version.score:.3f}"
            if version.score is not None and version.score >= 0.7
            else f"🟡 Score: {version.score:.3f}"
            if version.score is not None and version.score >= 0.4
            else f"🔴 Score: {version.score:.3f}"
            if version.score is not None
            else "⚪ No score"
        )

        tags_str = (
            " · ".join(f"`{t}`" for t in version.tags)
            if version.tags
            else "*no tags*"
        )

        with st.expander(
            f"**{version.id}** — {version.timestamp[:19].replace('T', ' ')}  |  {score_badge}"
        ):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"**ID:** `{version.id}`")
                st.markdown(
                    f"**Saved:** {version.timestamp[:19].replace('T', ' ')} UTC"
                )
                st.markdown(f"**Tags:** {tags_str}")
                if version.parent_id:
                    st.markdown(
                        f"**Parent version:** `{version.parent_id}`"
                    )
            with col_right:
                if version.score is not None:
                    st.metric(
                        label="Score",
                        value=f"{version.score:.3f}",
                    )

            st.markdown("**Prompt content:**")
            st.code(version.content, language=None)

            if version.metadata:
                with st.expander("Metadata"):
                    st.json(version.metadata)

    # ── Diff viewer ───────────────────────────────────────────────────────────
    if len(history) >= 2:
        st.divider()
        st.subheader("🔍 Compare Two Versions")
        st.markdown(
            "Select two versions to see exactly what changed between them."
        )

        version_ids   = [v.id for v in history]
        version_labels = [
            f"{v.id} — {v.timestamp[:19].replace('T', ' ')}"
            for v in history
        ]

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v1_label = st.selectbox(
                "Version A (older)",
                options=version_labels,
                index=0,
                key="diff_v1",
            )
        with col_v2:
            v2_label = st.selectbox(
                "Version B (newer)",
                options=version_labels,
                index=len(version_labels) - 1,
                key="diff_v2",
            )

        v1_id = version_ids[version_labels.index(v1_label)]
        v2_id = version_ids[version_labels.index(v2_label)]

        if st.button(
            "🔍  Show Diff",
            use_container_width=True,
        ):
            if v1_id == v2_id:
                st.warning("⚠️  Please select two different versions.")
            else:
                diff = vc.get_diff(v1_id, v2_id)
                st.markdown("**Diff output:**")
                st.code(diff, language="diff")

        # ── Performance comparison ────────────────────────────────────────────
        st.divider()
        st.subheader("📈 Performance Comparison")

        if st.button(
            "📊  Compare Performance",
            use_container_width=True,
        ):
            if v1_id == v2_id:
                st.warning(
                    "⚠️  Please select two different versions to compare."
                )
            else:
                comparison = vc.compare_performance(v1_id, v2_id)

                if "error" in comparison:
                    st.error(comparison["error"])
                else:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric(
                            label=f"Version A ({v1_id})",
                            value=f"{comparison['v1']['score']:.3f}",
                        )
                    with col_b:
                        st.metric(
                            label=f"Version B ({v2_id})",
                            value=f"{comparison['v2']['score']:.3f}",
                            delta=f"{comparison['improvement']:+.3f}",
                        )
                    with col_c:
                        better_id = comparison["better"]
                        if better_id == "tie":
                            st.metric(label="Winner", value="🤝 Tie")
                        elif better_id == v2_id:
                            st.metric(
                                label="Winner",
                                value="🏆 Version B",
                                delta=f"+{comparison['improvement_pct']:.1f}%",
                            )
                        else:
                            st.metric(
                                label="Winner",
                                value="🏆 Version A",
                                delta=f"{comparison['improvement_pct']:.1f}%",
                            )

    # ── Save new version manually ─────────────────────────────────────────────
    st.divider()
    st.subheader("💾 Save a New Version Manually")

    with st.form("save_version_form"):
        new_name    = st.text_input(
            "Prompt name",
            placeholder="e.g. complaint-classifier",
        )
        new_content = st.text_area(
            "Prompt content",
            height=120,
            placeholder="Paste your system prompt here…",
        )
        new_score   = st.number_input(
            "Score (optional)",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.01,
        )
        new_tags    = st.text_input(
            "Tags (comma separated, optional)",
            placeholder="e.g. v2, production, tested",
        )
        submitted   = st.form_submit_button(
            "💾  Save Version",
            use_container_width=True,
        )

    if submitted:
        if not new_name.strip():
            st.warning("⚠️  Please enter a prompt name.")
        elif not new_content.strip():
            st.warning("⚠️  Please enter the prompt content.")
        else:
            tags_list = (
                [t.strip() for t in new_tags.split(",") if t.strip()]
                if new_tags
                else []
            )
            saved = vc.save_version(
                name=new_name.strip(),
                content=new_content.strip(),
                score=new_score if new_score > 0 else None,
                tags=tags_list,
            )
            st.success(
                f"✅  Version `{saved.id}` saved successfully "
                f"for prompt *{saved.name}*."
            )
            st.rerun()
