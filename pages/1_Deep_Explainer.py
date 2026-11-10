"""
🔍 Deep Explainer — The Core RAG Engine
Time-aware hybrid retrieval, recency decay re-ranking,
and grounded multi-source synthesis with Gemini.
"""
import os
import time

import streamlit as st

import config
from shared import get_rag_engine, get_stats
from styles import inject_global_styles

# ─── Page Config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Deep Explainer | What Just Happened?",
    page_icon="🔍",
    layout="wide",
)
st.markdown(inject_global_styles(), unsafe_allow_html=True)

rag = get_rag_engine()
indexed_chunks = get_stats()

# ─── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Deep Explainer")
    st.caption("Hybrid RAG Synthesis Engine")
    st.markdown("---")

    env_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=env_key,
        type="password",
        key="api_key_explainer",
        help="Free key from https://aistudio.google.com/",
    )

    model_choice = st.selectbox(
        "Synthesis Model",
        options=["gemini-3.8-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
        index=0,
    )

    st.markdown("---")
    st.markdown("##### Temporal Constraints")
    time_filter = st.selectbox(
        "Publication Window",
        options=["All Monitored History", "Past 24 Hours", "Past 3 Days", "Past 7 Days"],
        index=0,
    )
    days_back_map = {
        "All Monitored History": None,
        "Past 24 Hours": 1,
        "Past 3 Days": 3,
        "Past 7 Days": 7,
    }
    days_back = days_back_map[time_filter]

    recency_decay = st.slider(
        "Recency Bias (λ)",
        min_value=0.0, max_value=0.2, value=0.05, step=0.01,
        help="Score × exp(−λ × days_elapsed)",
    )
    top_k = st.slider("Context Depth", min_value=5, max_value=25, value=12, step=1)

    st.markdown("---")
    st.markdown(
        f"""
    <div class="metric-box">
        <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700;">Index Size</div>
        <div style="font-family: var(--font-mono); font-size: 1.4rem; font-weight: 500; color: var(--text-primary); margin-top: 4px;">{indexed_chunks} chunks</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ─── Hero ─────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero-wrap">
    <div class="hero-eyebrow">
        <span class="hero-pulse"></span>
        <span>Deep Explainer &bull; Hybrid BM25 + Dense Retrieval</span>
    </div>
    <h1 class="hero-title">Investigate Any Story</h1>
    <p class="hero-subtitle">
        Ask about any breaking event. The engine retrieves and re-ranks passages with time-aware hybrid search,
        then synthesizes a grounded brief with consensus/conflict detection and chronological timeline.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Example Query Pills ─────────────────────────────────────────
example_queries = [
    "What is happening with the Krakow shooting?",
    "What are the reports on train accidents in Europe?",
    "What did the Pope say regarding economic austerity?",
    "Latest diplomatic talks and ceasefire status",
]

st.markdown(
    '<div class="section-label">Suggested Inquiries</div>',
    unsafe_allow_html=True,
)
cols = st.columns(len(example_queries))
selected_example = None
for i, col in enumerate(cols):
    if col.button(example_queries[i], key=f"explainer_ex_{i}", use_container_width=True):
        selected_example = example_queries[i]

user_query = st.text_input(
    "Ask:",
    value=selected_example or "",
    placeholder="e.g. What happened in the Krakow shooting? What is the status of Ukraine peace talks?",
    label_visibility="collapsed",
)

# ─── RAG Pipeline ─────────────────────────────────────────────────
if user_query:
    with st.spinner("Executing hybrid retrieval & synthesizing brief..."):
        start_time = time.time()
        try:
            result = rag.generate_explanation(
                query=user_query,
                days_back=days_back,
                top_k=top_k,
                api_key=api_key_input,
                model_name=model_choice,
            )
        except TypeError:
            result = rag.generate_explanation(
                query=user_query,
                days_back=days_back,
                top_k=top_k,
                api_key=api_key_input,
            )
        elapsed = time.time() - start_time

    sources = result["sources"]
    unique_outlets = sorted(list(set(s.get("source", "") for s in sources if s.get("source"))))
    corroboration_score = min(100, int((len(unique_outlets) / max(len(unique_outlets), 3)) * 85 + min(len(sources), 5) * 3))
    corroboration_label = "High Multi-Wire Consensus" if len(unique_outlets) >= 3 else ("Moderate Cross-Wire Support" if len(unique_outlets) == 2 else "Single-Outlet Report")

    # ─── Tabs ─────────────────────────────────────────────────────
    tab_brief, tab_sources, tab_timeline, tab_audit = st.tabs(
        ["📋 Executive Brief", "📚 Source Dossier", "⏳ Chronology & Scrubber", "🔍 Diagnostics"]
    )

    with tab_brief:
        st.markdown(
            f"""
        <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 180px; background: var(--bg-surface); border: 1px solid var(--border-faint); border-radius: var(--radius-md); padding: 12px 16px;">
                <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Corroboration Level</div>
                <div style="font-size: 1.05rem; font-weight: 600; color: var(--text-primary); margin-top: 2px;">{corroboration_label}</div>
                <div style="font-size: 0.72rem; color: var(--accent-sage); margin-top: 2px;">{len(unique_outlets)} Independent Outlets &bull; {len(sources)} Passages</div>
            </div>
            <div style="flex: 1; min-width: 180px; background: var(--bg-surface); border: 1px solid var(--border-faint); border-radius: var(--radius-md); padding: 12px 16px;">
                <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Corroborating Wires</div>
                <div style="font-size: 0.92rem; font-weight: 500; color: var(--text-secondary); margin-top: 4px;">{', '.join(unique_outlets)}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: var(--bg-surface); border: 1px solid var(--border-faint); border-radius: var(--radius-md); padding: 12px 16px;">
                <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Inference Latency</div>
                <div style="font-family: var(--font-mono); font-size: 1.05rem; font-weight: 600; color: var(--text-primary); margin-top: 2px;">{elapsed:.2f}s</div>
                <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">Model: {model_choice}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="synthesis-card">{result["answer"]}</div>', unsafe_allow_html=True)

    with tab_sources:
        st.markdown(
            f'<div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 16px;">'
            f'Showing {len(sources)} passage chunks ranked by BM25 + dense fusion with recency decay.</div>',
            unsafe_allow_html=True,
        )
        if not sources:
            st.info("No source passages retrieved.")
        else:
            for i, src in enumerate(sources, 1):
                norm_score = min(1.0, max(0.1, src.get("score", 0.5) * 2.0)) * 100
                st.markdown(
                    f"""
                <div class="dossier-card" style="animation-delay: {i * 0.04}s;">
                    <div class="dossier-header">
                        <span class="source-tag">{src['source']}</span>
                        <span class="time-tag">{src['published_date'][:10]} &bull; {src['days_ago']}d ago</span>
                    </div>
                    <div class="dossier-title">[Source {i}] <a href="{src['url']}" target="_blank">{src['title']} &nearr;</a></div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.73rem; color: var(--text-muted); margin-top: 6px;">
                        <span>Hybrid Score: {src['score']:.4f} (RRF: {src['rrf_score']:.4f})</span>
                        <span>{int(norm_score)}% match</span>
                    </div>
                    <div class="match-bar-bg"><div class="match-bar-fill" style="width: {norm_score:.1f}%;"></div></div>
                    <div class="dossier-text">{src['text']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    with tab_timeline:
        st.markdown(
            '<div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 14px;">'
            'Chronological event reconstruction from retrieved source timestamps. Step through the slider to observe how breaking reports developed over time.</div>',
            unsafe_allow_html=True,
        )
        if not sources:
            st.info("No timeline items available.")
        else:
            chrono = sorted(sources, key=lambda x: x.get("published_date", ""))

            # Interactive Scrubber
            if len(chrono) > 1:
                st.markdown('<div class="section-label">Interactive Story Scrubber</div>', unsafe_allow_html=True)
                step = st.slider("Milestone Progress", 1, len(chrono), len(chrono), key="timeline_scrubber_slider")
                active_src = chrono[step - 1]
                active_pub = active_src.get("published_date", "")[:16].replace("T", " ")
                st.markdown(
                    f"""
                    <div class="dossier-card" style="border-left: 3px solid var(--accent-warm); margin-bottom: 24px;">
                        <div style="font-size: 0.68rem; color: var(--accent-warm); text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Active Event Focus &bull; Step {step} of {len(chrono)}</div>
                        <div style="font-size: 1.05rem; font-weight: 600; color: var(--text-primary); margin: 6px 0;">{active_src['title']}</div>
                        <div style="font-size: 0.76rem; color: var(--text-muted); margin-bottom: 10px;">{active_pub} &bull; {active_src['source']} &bull; <a href="{active_src['url']}" target="_blank" style="color: var(--text-secondary);">Read Original Dispatch &nearr;</a></div>
                        <div class="dossier-text">{active_src['text']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="section-label">Full Chronological Timeline</div>', unsafe_allow_html=True)
            tl_html = '<div class="timeline-wrap">'
            for src in chrono:
                pub = src.get("published_date", "")[:16].replace("T", " ")
                tl_html += f"""
                <div class="timeline-node">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">{pub} &bull; {src['source']}</div>
                    <div class="timeline-headline">{src['title']}</div>
                    <div class="timeline-body">{src['text'][:220]}... [<a href="{src['url']}" target="_blank">Read Wire</a>]</div>
                </div>
                """
            tl_html += "</div>"
            st.markdown(tl_html, unsafe_allow_html=True)

    with tab_audit:
        st.markdown("##### Retrieval Pipeline Diagnostics")
        st.markdown(
            f"""
        - **Date Filter:** `days_back = {days_back}`
        - **Recency Decay (λ):** `{recency_decay}`
        - **Dense Model:** `{config.DENSE_MODEL_NAME}`
        - **Sparse Model:** `{config.SPARSE_MODEL_NAME}`
        - **Fusion:** Reciprocal Rank Fusion (RRF)
        """
        )
        with st.expander("Inspect Raw LLM Prompt"):
            st.code(result["prompt"], language="markdown")
