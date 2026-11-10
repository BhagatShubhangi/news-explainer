"""
⚖️ Cross-Wire Analysis — Media Framing & Omission Detector
Compare how different outlets covered the same story.
Identifies emphasis differences, omissions, and tonal framing.
"""
import os
import time
from collections import defaultdict

import streamlit as st

import config
from shared import get_rag_engine, get_all_articles
from styles import inject_global_styles

try:
    from google import genai
except ImportError:
    genai = None

# ─── Page Config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Cross-Wire Analysis | What Just Happened?",
    page_icon="⚖️",
    layout="wide",
)
st.markdown(inject_global_styles(), unsafe_allow_html=True)

rag = get_rag_engine()

# ─── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚖️ Cross-Wire Analysis")
    st.caption("Media Framing & Omission Detector")
    st.markdown("---")

    env_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=env_key,
        type="password",
        key="api_key_crosswire",
    )

    model_choice = st.selectbox(
        "Analysis Model",
        options=["gemini-3.8-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
        index=0,
        key="crosswire_model",
    )

# ─── Hero ─────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero-wrap">
    <div class="hero-eyebrow">
        <span class="hero-pulse"></span>
        <span>Cross-Wire Analysis &bull; Multi-Source Framing Comparison</span>
    </div>
    <h1 class="hero-title">How Different Outlets<br>Told the Same Story</h1>
    <p class="hero-subtitle">
        Select a topic and two wire services. The engine retrieves each outlet's coverage
        and performs a structured framing diff — identifying emphasis, omissions, tone shifts,
        and narrative divergence.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Retrieve all articles and group by source ────────────────────
articles = get_all_articles()
source_articles = defaultdict(list)
for art in articles:
    source_articles[art.get("source", "Unknown")].append(art)

available_sources = sorted(source_articles.keys())

if len(available_sources) < 2:
    st.warning("Need at least 2 different wire sources indexed to run a cross-wire comparison.")
    st.stop()

# ─── Suggested Overlapping Stories ───────────────────────────────
st.markdown('<div class="section-label">Preset Cross-Outlet Stories</div>', unsafe_allow_html=True)
preset_cols = st.columns(3)
preset_query = None
preset_src_a = None
preset_src_b = None

if preset_cols[0].button("Krakow Shooting: BBC vs. Al Jazeera", use_container_width=True, key="preset_krakow"):
    preset_query = "Krakow shooting suspect"
    preset_src_a = "BBC World"
    preset_src_b = "Al Jazeera"
if preset_cols[1].button("Pope & Milei: BBC vs. Deutsche Welle", use_container_width=True, key="preset_pope"):
    preset_query = "Pope Leo Milei austerity"
    preset_src_a = "BBC World"
    preset_src_b = "Deutsche Welle"
if preset_cols[2].button("Nvidia Investigation: NPR vs. DW", use_container_width=True, key="preset_nvidia"):
    preset_query = "Nvidia CEO Huang investigation"
    preset_src_a = "NPR News"
    preset_src_b = "Deutsche Welle"

# ─── Controls ─────────────────────────────────────────────────────
st.markdown("")
st.markdown('<div class="section-label">Configure Custom Comparison</div>', unsafe_allow_html=True)

col_topic, col_src_a, col_src_b = st.columns([2, 1, 1])

with col_topic:
    topic_query = st.text_input(
        "Story / Topic to Compare",
        value=preset_query or "",
        placeholder="e.g. Krakow shooting, Pope Leo economic speech, Ukraine ceasefire talks",
        label_visibility="collapsed",
    )

with col_src_a:
    idx_a = available_sources.index(preset_src_a) if preset_src_a in available_sources else 0
    source_a = st.selectbox("Outlet A", options=available_sources, index=idx_a)

with col_src_b:
    if preset_src_b in available_sources:
        idx_b = available_sources.index(preset_src_b)
    else:
        idx_b = 1 if len(available_sources) > 1 else 0
    source_b = st.selectbox("Outlet B", options=available_sources, index=idx_b)


# ─── Run Comparison ───────────────────────────────────────────────
if topic_query and source_a and source_b and source_a != source_b:
    key = api_key_input or os.environ.get("GEMINI_API_KEY")

    # Retrieve chunks from each specific source
    with st.spinner("Retrieving source-specific passages..."):
        from qdrant_client import models as qmodels

        def retrieve_source_chunks(query, source_name, top_k=6):
            query_dense = list(rag.dense_model.embed([query]))[0].tolist()
            query_sparse = list(rag.sparse_model.embed([query]))[0]
            source_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="source",
                        match=qmodels.MatchValue(value=source_name),
                    )
                ]
            )
            results = rag.client.query_points(
                collection_name=config.COLLECTION_NAME,
                prefetch=[
                    qmodels.Prefetch(
                        query=qmodels.SparseVector(
                            indices=query_sparse.indices.tolist(),
                            values=query_sparse.values.tolist(),
                        ),
                        using="sparse",
                        limit=top_k * 2,
                        filter=source_filter,
                    ),
                    qmodels.Prefetch(
                        query=query_dense,
                        using="dense",
                        limit=top_k * 2,
                        filter=source_filter,
                    ),
                ],
                query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
                limit=top_k,
            )
            return [
                {
                    "title": p.payload.get("title", ""),
                    "source": p.payload.get("source", ""),
                    "text": p.payload.get("text", ""),
                    "url": p.payload.get("url", ""),
                    "published_date": p.payload.get("published_date", ""),
                    "score": p.score or 0,
                }
                for p in results.points
            ]

        chunks_a = retrieve_source_chunks(topic_query, source_a)
        chunks_b = retrieve_source_chunks(topic_query, source_b)

    if not chunks_a and not chunks_b:
        st.info("Neither outlet has relevant coverage for this topic in the index.")
        st.stop()

    # Build context strings
    context_a = "\n\n".join(
        f"[{source_a} #{i+1}] {c['title']}\nDate: {c['published_date']}\n{c['text']}"
        for i, c in enumerate(chunks_a)
    )
    context_b = "\n\n".join(
        f"[{source_b} #{i+1}] {c['title']}\nDate: {c['published_date']}\n{c['text']}"
        for i, c in enumerate(chunks_b)
    )

    comparison_prompt = f"""You are an expert media analyst performing a structured cross-source framing comparison.

TOPIC: "{topic_query}"

OUTLET A — {source_a}:
{context_a if context_a.strip() else "[No relevant coverage found from this outlet]"}

OUTLET B — {source_b}:
{context_b if context_b.strip() else "[No relevant coverage found from this outlet]"}

Produce a structured Markdown analysis with these exact sections:

### 1. Coverage Overlap
Bullet points of key facts that BOTH outlets reported. Note where they agree.

### 2. Emphasis & Angle Differences
For each outlet, describe its dominant framing angle (e.g., security/legal, humanitarian, geopolitical, economic, human interest). Quote specific language choices that reveal this framing.

### 3. The Omission Battlefield
- **What {source_a} covered that {source_b} did NOT mention** (specific facts, quotes, or angles).
- **What {source_b} covered that {source_a} did NOT mention**.

### 4. Tone & Language Analysis
Compare the emotional register and word choices:
- Does one outlet use more charged/emotive language?
- Does one outlet attribute actions differently (passive vs. active voice)?
- Are headlines framed differently?

### 5. Key Takeaway
A 2-3 sentence objective summary of how a reader's understanding would differ depending on which outlet they read.

RULES:
- Be strictly objective. Do not declare one outlet "better" or "more accurate."
- Ground every observation in specific passages from the retrieved text.
- If one outlet has no coverage, note this as a significant finding itself.
"""

    # Generate comparison
    if not key:
        st.warning("Please enter your Gemini API key in the sidebar to generate the framing analysis.")

        # Still show the raw retrieved passages
        st.markdown('<div class="section-label">Retrieved Passages</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{source_a}** ({len(chunks_a)} passages)")
            for c in chunks_a:
                st.markdown(f'<div class="dossier-text">{c["text"][:300]}</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown(f"**{source_b}** ({len(chunks_b)} passages)")
            for c in chunks_b:
                st.markdown(f'<div class="dossier-text">{c["text"][:300]}</div>', unsafe_allow_html=True)
        st.stop()

    with st.spinner(f"Analyzing framing divergence between {source_a} and {source_b}..."):
        start_time = time.time()
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=model_choice,
                contents=comparison_prompt,
            )
            analysis_text = response.text
        except Exception as e:
            analysis_text = f"**Error:** {e}"
        elapsed = time.time() - start_time

    # ─── Results ──────────────────────────────────────────────────
    st.markdown(
        f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;
                border-bottom: 1px solid var(--border-faint); margin-bottom: 16px;">
        <div style="font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-muted);">
            Framing Analysis: {source_a} vs. {source_b}
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">
            {elapsed:.2f}s &bull; {model_choice} &bull; {len(chunks_a) + len(chunks_b)} passages analyzed
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="synthesis-card">{analysis_text}</div>', unsafe_allow_html=True)

    # Show raw passages side by side
    st.markdown("")
    st.markdown('<div class="section-label">Raw Source Passages Used</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            f'<div style="font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 10px;">'
            f'{source_a} — {len(chunks_a)} passages</div>',
            unsafe_allow_html=True,
        )
        for i, c in enumerate(chunks_a):
            st.markdown(
                f"""
            <div class="dossier-card" style="animation-delay: {i * 0.05}s;">
                <div class="dossier-title"><a href="{c['url']}" target="_blank">{c['title']} &nearr;</a></div>
                <div class="dossier-text">{c['text']}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col_b:
        st.markdown(
            f'<div style="font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 10px;">'
            f'{source_b} — {len(chunks_b)} passages</div>',
            unsafe_allow_html=True,
        )
        for i, c in enumerate(chunks_b):
            st.markdown(
                f"""
            <div class="dossier-card" style="animation-delay: {i * 0.05}s;">
                <div class="dossier-title"><a href="{c['url']}" target="_blank">{c['title']} &nearr;</a></div>
                <div class="dossier-text">{c['text']}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

elif topic_query and source_a == source_b:
    st.warning("Please select two **different** outlets to compare.")
