"""
🌐 Intelligence Radar — The Landing Hub
Auto-clusters ingested articles, displays a live wire ticker,
trending topic cards, source diagnostics, and a recent wire feed.
"""
import os
import time
from datetime import datetime, timezone

import streamlit as st

import config
from shared import get_rag_engine, get_stats, get_all_articles, cluster_articles, get_source_counts
from ingest import NewsIngestor
from styles import inject_global_styles

# ─── Page Config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="What Just Happened? | Intelligence Radar",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(inject_global_styles(), unsafe_allow_html=True)

rag = get_rag_engine()
indexed_chunks = get_stats()

# ─── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📰 What Just Happened?")
    st.caption("Investigative News Explainer")
    st.markdown("---")

    env_key = os.environ.get("GEMINI_API_KEY", "")
    st.text_input(
        "Gemini API Key",
        value=env_key,
        type="password",
        key="api_key_sidebar",
        help="Free key from https://aistudio.google.com/",
    )

    st.markdown("---")
    st.markdown("##### Index Status")
    st.markdown(
        f"""
    <div class="metric-box">
        <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700;">Total Indexed Chunks</div>
        <div style="font-family: var(--font-mono); font-size: 1.6rem; font-weight: 500; color: var(--text-primary); margin-top: 4px;">{indexed_chunks}</div>
        <div style="font-size: 0.73rem; color: var(--text-tertiary); margin-top: 4px;">Hybrid BM25 + Dense BGE</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Pull & Ingest Latest Wires", use_container_width=True):
        with st.spinner("Fetching RSS feeds..."):
            ingestor = NewsIngestor(client=rag.client)
            new_count = ingestor.run_all()
            st.success(f"Indexed {new_count} new articles.")
            time.sleep(0.8)
            st.rerun()


# ─── Data ─────────────────────────────────────────────────────────
articles = get_all_articles()
clusters = cluster_articles(articles, max_clusters=6)
source_counts = get_source_counts(articles)
now = datetime.now(timezone.utc)

# ─── Wire Ticker ──────────────────────────────────────────────────
if articles:
    sorted_arts = sorted(articles, key=lambda a: a.get("published_timestamp", 0), reverse=True)
    ticker_items = ""
    for art in sorted_arts[:20]:
        title = art.get("title", "")[:80]
        src = art.get("source", "")
        url = art.get("url", "#")
        ticker_items += f"""
            <div class="wire-ticker-item">
                <span class="wire-ticker-src">{src}</span>
                <a href="{url}" target="_blank">{title}</a>
                <span class="wire-ticker-dot"></span>
            </div>
        """
    # Duplicate for seamless infinite scroll
    st.markdown(
        f"""
    <div class="wire-ticker-wrap">
        <div class="wire-ticker-track">
            {ticker_items}
            {ticker_items}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ─── Hero ─────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="hero-wrap">
    <div class="hero-eyebrow">
        <span class="hero-pulse"></span>
        <span>Intelligence Radar Active &bull; {len(articles)} Articles Monitored &bull; {len(source_counts)} Wire Services</span>
    </div>
    <h1 class="hero-title">What Just Happened?</h1>
    <p class="hero-subtitle">
        Multi-source investigative news explainer. Auto-clusters breaking stories across global wire services,
        isolates verified consensus from developing claims, and reconstructs chronological event timelines.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Quick Stats Row ─────────────────────────────────────────────
st.markdown(
    f"""
<div class="stat-row">
    <div class="stat-card">
        <div class="stat-label">Articles Indexed</div>
        <div class="stat-value">{len(articles)}</div>
        <div class="stat-sub">Unique articles across all feeds</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Wire Services</div>
        <div class="stat-value">{len(source_counts)}</div>
        <div class="stat-sub">{', '.join(list(source_counts.keys())[:4])}{'...' if len(source_counts) > 4 else ''}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Active Storylines</div>
        <div class="stat-value">{len([c for c in clusters if c['topic'] != 'Other Developments'])}</div>
        <div class="stat-sub">Auto-detected topic clusters</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Vector Chunks</div>
        <div class="stat-value">{indexed_chunks}</div>
        <div class="stat-sub">BM25 + BGE-Small hybrid index</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Topic Clusters ──────────────────────────────────────────────
st.markdown('<div class="section-label">Trending Storylines &mdash; Auto-Clustered Topics</div>', unsafe_allow_html=True)

if clusters:
    cluster_html = '<div class="cluster-grid">'
    for idx, cl in enumerate(clusters):
        topic = cl["topic"]
        count = cl["count"]
        sources_str = ", ".join(sorted(cl["sources"]))
        keywords_html = "".join(f'<span class="cluster-kw">{kw}</span>' for kw in cl.get("keywords", [])[:5])

        # Show top 2 headlines
        headlines_html = ""
        for art in cl["articles"][:3]:
            title = art.get("title", "")[:90]
            url = art.get("url", "#")
            headlines_html += f'<div style="margin-bottom: 4px;">→ <a href="{url}" target="_blank">{title}</a></div>'

        cluster_html += f"""
        <div class="cluster-card stagger-{min(idx+1, 6)}">
            <div class="cluster-topic">{topic}</div>
            <div class="cluster-meta">
                <span class="cluster-count">{count} article{'s' if count != 1 else ''}</span>
                <span class="cluster-sources">{sources_str}</span>
            </div>
            <div class="cluster-kw-list">{keywords_html}</div>
            <div class="cluster-headline">{headlines_html}</div>
        </div>
        """
    cluster_html += "</div>"
    st.markdown(cluster_html, unsafe_allow_html=True)
else:
    st.info("No articles indexed yet. Click **Pull & Ingest Latest Wires** in the sidebar.")

# ─── Source Distribution ─────────────────────────────────────────
st.markdown('<div class="section-label">Wire Source Distribution</div>', unsafe_allow_html=True)

if source_counts:
    max_count = max(source_counts.values()) if source_counts else 1
    dist_html = ""
    for src_name, cnt in source_counts.items():
        pct = (cnt / max_count) * 100
        dist_html += f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <div style="min-width: 140px; font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); text-align: right;">{src_name}</div>
            <div style="flex: 1; height: 6px; background: rgba(255,255,255,0.04); border-radius: 3px; overflow: hidden;">
                <div style="width: {pct:.1f}%; height: 100%; background: linear-gradient(90deg, var(--accent-steel), var(--accent-warm)); border-radius: 3px; transition: width 0.6s var(--ease-out-expo);"></div>
            </div>
            <div style="min-width: 30px; font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted);">{cnt}</div>
        </div>
        """
    st.markdown(dist_html, unsafe_allow_html=True)

# ─── Recent Wire Feed ────────────────────────────────────────────
st.markdown("")
st.markdown('<div class="section-label">Latest Wire Dispatches</div>', unsafe_allow_html=True)

if articles:
    sorted_recent = sorted(articles, key=lambda a: a.get("published_timestamp", 0), reverse=True)
    feed_html = ""
    for idx, art in enumerate(sorted_recent[:15]):
        title = art.get("title", "")
        source = art.get("source", "")
        url = art.get("url", "#")
        pub_ts = art.get("published_timestamp", 0)
        if pub_ts:
            elapsed_hrs = (now.timestamp() - pub_ts) / 3600
            if elapsed_hrs < 1:
                time_str = f"{int(elapsed_hrs * 60)}m"
                time_unit = "ago"
            elif elapsed_hrs < 24:
                time_str = f"{int(elapsed_hrs)}h"
                time_unit = "ago"
            else:
                time_str = f"{int(elapsed_hrs / 24)}d"
                time_unit = "ago"
        else:
            time_str = "—"
            time_unit = ""

        feed_html += f"""
        <div class="wire-item" style="animation-delay: {idx * 0.04}s;">
            <div class="wire-time-col">
                <div class="wire-time-val">{time_str}</div>
                <div class="wire-time-unit">{time_unit}</div>
            </div>
            <div class="wire-body">
                <div class="wire-body-title"><a href="{url}" target="_blank">{title}</a></div>
                <div class="wire-body-source">{source}</div>
            </div>
        </div>
        """
    st.markdown(feed_html, unsafe_allow_html=True)
else:
    st.info("No articles available. Ingest feeds to populate this view.")
