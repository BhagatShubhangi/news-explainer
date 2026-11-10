"""
🕸️ Entity Graph — Interactive Knowledge Network
Extracts people, organizations, and locations from indexed articles
and renders an interactive network graph showing connections.
"""
import os
import re
from collections import Counter, defaultdict

import streamlit as st
import streamlit.components.v1 as components

import config
from shared import get_rag_engine, get_all_articles
from styles import inject_global_styles

# ─── Page Config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Entity Graph | What Just Happened?",
    page_icon="🕸️",
    layout="wide",
)
st.markdown(inject_global_styles(), unsafe_allow_html=True)

rag = get_rag_engine()

# ─── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🕸️ Entity Graph")
    st.caption("Interactive Knowledge Network")
    st.markdown("---")
    min_mentions = st.slider("Min Mentions to Display", 1, 5, 2, key="graph_min")
    max_nodes = st.slider("Max Nodes", 20, 80, 40, key="graph_max")

# ─── Hero ─────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero-wrap">
    <div class="hero-eyebrow">
        <span class="hero-pulse"></span>
        <span>Entity Graph &bull; Knowledge Network Visualization</span>
    </div>
    <h1 class="hero-title">Who's Connected to What</h1>
    <p class="hero-subtitle">
        Extracts named entities — people, organizations, and places — from all indexed articles,
        maps co-occurrence relationships, and renders an interactive network to reveal hidden connections.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Entity Extraction ───────────────────────────────────────────
@st.cache_data(ttl=300)
def extract_entities_from_articles():
    """Extract entities using spaCy NER from article titles and texts."""
    articles = get_all_articles()
    if not articles:
        return {}, {}, []

    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # Fallback: simple capitalized phrase extraction
        nlp = None

    entity_counts = Counter()          # entity_text -> count
    entity_types = {}                  # entity_text -> type (PERSON, ORG, GPE)
    co_occurrences = Counter()         # (entity_a, entity_b) -> count
    article_entities_list = []         # list of (article, [entities])

    for art in articles:
        text = art.get("title", "") + ". " + (art.get("text", "") or "")[:500]
        article_ents = set()

        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("PERSON", "ORG", "GPE", "NORP", "LOC", "FAC", "EVENT"):
                    name = ent.text.strip()
                    if len(name) > 2 and len(name) < 50:
                        entity_counts[name] += 1
                        entity_types[name] = ent.label_
                        article_ents.add(name)
        else:
            # Simple fallback: extract capitalized multi-word phrases
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            for w in words:
                if len(w) > 3:
                    entity_counts[w] += 1
                    entity_types[w] = "MISC"
                    article_ents.add(w)

        article_entities_list.append((art, list(article_ents)))

        # Co-occurrence: entities appearing in same article are connected
        sorted_ents = sorted(article_ents)
        for i in range(len(sorted_ents)):
            for j in range(i + 1, len(sorted_ents)):
                co_occurrences[(sorted_ents[i], sorted_ents[j])] += 1

    return entity_counts, entity_types, co_occurrences, article_entities_list


result = extract_entities_from_articles()
if len(result) == 4:
    entity_counts, entity_types, co_occurrences, article_entities_list = result
else:
    entity_counts, entity_types, co_occurrences, article_entities_list = {}, {}, Counter(), []

if not entity_counts:
    st.info("No entities extracted. Ensure articles are indexed and spaCy `en_core_web_sm` is installed.")
    st.stop()

# ─── Filter entities by min mentions ─────────────────────────────
filtered_entities = {k: v for k, v in entity_counts.most_common() if v >= min_mentions}
top_entities = dict(list(filtered_entities.items())[:max_nodes])

# ─── Stats ────────────────────────────────────────────────────────
type_counts = Counter()
for ent, etype in entity_types.items():
    if ent in top_entities:
        type_counts[etype] += 1

st.markdown(
    f"""
<div class="stat-row">
    <div class="stat-card">
        <div class="stat-label">Total Entities</div>
        <div class="stat-value">{len(entity_counts)}</div>
        <div class="stat-sub">Extracted via NER</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Displayed Nodes</div>
        <div class="stat-value">{len(top_entities)}</div>
        <div class="stat-sub">≥ {min_mentions} mentions</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">People</div>
        <div class="stat-value">{type_counts.get('PERSON', 0)}</div>
        <div class="stat-sub">Named individuals</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Places</div>
        <div class="stat-value">{type_counts.get('GPE', 0) + type_counts.get('LOC', 0)}</div>
        <div class="stat-sub">Countries, cities, regions</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Build Interactive Graph (pure HTML/JS with vis.js) ──────────
st.markdown('<div class="section-label">Interactive Entity Network</div>', unsafe_allow_html=True)

# Color mapping for entity types (muted tones)
type_colors = {
    "PERSON": "#B0846A",   # terracotta
    "ORG": "#8494A7",      # steel
    "GPE": "#7A9E87",      # sage
    "LOC": "#7A9E87",      # sage
    "NORP": "#9B8EC4",     # lavender
    "FAC": "#A89070",      # warm brown
    "EVENT": "#BFA07A",    # gold sand
    "MISC": "#8494A7",     # steel
}

# Build nodes JSON
nodes_js = []
for ent, count in top_entities.items():
    etype = entity_types.get(ent, "MISC")
    color = type_colors.get(etype, "#8494A7")
    size = min(8 + count * 3, 35)
    nodes_js.append(
        f'{{id: "{ent}", label: "{ent}", size: {size}, color: "{color}", '
        f'font: {{color: "#E0E4EA", size: 11}}, title: "{etype}: {count} mentions"}}'
    )

# Build edges JSON
edges_js = []
for (a, b), weight in co_occurrences.items():
    if a in top_entities and b in top_entities and weight >= 1:
        thickness = min(1 + weight, 5)
        edges_js.append(
            f'{{from: "{a}", to: "{b}", width: {thickness}, '
            f'color: {{color: "rgba(255,255,255,0.08)", highlight: "rgba(191,160,122,0.5)"}}}}'
        )

graph_html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #0A0D12;
            overflow: hidden;
        }}
        #graph-container {{
            width: 100%;
            height: 580px;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            background: #0E1219;
        }}
        .legend {{
            position: absolute;
            bottom: 16px;
            left: 16px;
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-family: 'Inter', sans-serif;
            font-size: 11px;
            color: #8B95A5;
        }}
        .legend-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <div id="graph-container"></div>
    <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background: #B0846A;"></div> Person</div>
        <div class="legend-item"><div class="legend-dot" style="background: #8494A7;"></div> Organization</div>
        <div class="legend-item"><div class="legend-dot" style="background: #7A9E87;"></div> Place</div>
        <div class="legend-item"><div class="legend-dot" style="background: #9B8EC4;"></div> Group / Nationality</div>
        <div class="legend-item"><div class="legend-dot" style="background: #BFA07A;"></div> Event</div>
    </div>
    <script>
        var nodes = new vis.DataSet([{", ".join(nodes_js)}]);
        var edges = new vis.DataSet([{", ".join(edges_js)}]);
        var container = document.getElementById('graph-container');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            physics: {{
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {{
                    gravitationalConstant: -40,
                    centralGravity: 0.006,
                    springLength: 140,
                    springConstant: 0.04,
                    damping: 0.4,
                    avoidOverlap: 0.6
                }},
                stabilization: {{ iterations: 120 }}
            }},
            nodes: {{
                shape: 'dot',
                borderWidth: 0,
                shadow: {{ enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 }}
            }},
            edges: {{
                smooth: {{ type: 'continuous' }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                navigationButtons: false,
                keyboard: false
            }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>
"""

components.html(graph_html, height=620)

# ─── Entity Table ─────────────────────────────────────────────────
st.markdown("")
st.markdown('<div class="section-label">Entity Frequency Table</div>', unsafe_allow_html=True)

table_html = ""
for ent, count in list(top_entities.items())[:30]:
    etype = entity_types.get(ent, "MISC")
    color = type_colors.get(etype, "#8494A7")
    bar_width = min(count / max(top_entities.values()) * 100, 100)
    table_html += f"""
    <div style="display: flex; align-items: center; gap: 12px; padding: 7px 0; border-bottom: 1px solid var(--border-faint);">
        <div style="min-width: 10px; width: 10px; height: 10px; border-radius: 50%; background: {color}; flex-shrink: 0;"></div>
        <div style="min-width: 180px; font-size: 0.88rem; font-weight: 600; color: var(--text-primary);">{ent}</div>
        <div style="min-width: 55px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--text-muted);">{etype}</div>
        <div style="flex: 1; height: 4px; background: rgba(255,255,255,0.04); border-radius: 2px; overflow: hidden;">
            <div style="width: {bar_width:.1f}%; height: 100%; background: {color}; opacity: 0.6; border-radius: 2px;"></div>
        </div>
        <div style="min-width: 30px; font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted); text-align: right;">{count}</div>
    </div>
    """

st.markdown(table_html, unsafe_allow_html=True)
