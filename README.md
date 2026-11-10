# 📰 "What Just Happened?" — Time-Aware News Explainer RAG

An open-source, production-grade Retrieval-Augmented Generation (RAG) system that answers questions about recent news events. Built to solve real-world RAG challenges: **temporal decay**, **hybrid retrieval (BM25 + Dense)**, **source deduplication**, and **consensus vs. conflict breakdown**.

---

## 🌟 Key Features & Architectural Highlights

1. **Native Hybrid Search (Dense + Sparse BM25 via RRF)**:
   - Uses `fastembed` with `BAAI/bge-small-en-v1.5` for dense semantics and `Qdrant/bm25` for sparse keyword recall.
   - Merges results using Qdrant's native **Reciprocal Rank Fusion (RRF)**. Exact named entities (e.g. *Krakow*, *Nvidia*, *Milei*) are never missed.
2. **Time-Aware Scoring & Recency Decay**:
   - Standard vector search is "time blind". We apply an exponential recency decay multiplier:
     $$\text{Final Score} = \text{RRF Score} \times e^{-\lambda \times \Delta t}$$
     where $\Delta t$ is days elapsed since publication and $\lambda$ is a tunable parameter.
3. **The "Fog of War" Consensus & Conflict Detection**:
   - Rather than blending conflicting narratives, the LLM prompt explicitly identifies:
     - **Verified Facts / Consensus:** Points where multiple outlets agree.
     - **Disputed / Unclear:** Contradictory casualty figures, unverified claims, and developing story angles.
4. **Story Chronology (Timeline Extraction)**:
   - Orders retrieved context chronologically to construct an event progression timeline.
5. **100% Free & Open-Source Stack**:
   - **Embeddings:** Local CPU-based FastEmbed (no API costs).
   - **Vector Database:** Local Qdrant Embedded (no Docker or cloud subscription required).
   - **LLM Synthesis:** Google Gemini 2.0 / 1.5 Flash via Google AI Studio free tier.
   - **Automation:** GitHub Actions cron schedule.

---

## 📂 Platform Architecture & Multi-Page Workspaces

```
news-explainer/
├── app.py                     # 🌐 Workspace 1: Intelligence Radar & Live Wire Ticker
├── pages/
│   ├── 1_Deep_Explainer.py    # 🔍 Workspace 2: Grounded RAG + Story Milestone Scrubber
│   ├── 2_Cross_Wire_Analysis.py# ⚖️ Workspace 3: Multi-Source Framing & Omission Diff
│   └── 3_Entity_Graph.py      # 🕸️ Workspace 4: Interactive Knowledge Network Graph
├── config.py                  # Global settings, paths, and model hyperparameters
├── shared.py                  # Singleton RAG engine, clustering & caching layer
├── styles.py                  # Design tokens, typography (Newsreader + Inter) & animations
├── eval_benchmark.py          # 20-question retrieval & precision benchmark suite
├── feeds.json                 # Monitored RSS feeds (BBC, NPR, The Hindu, DW, Al Jazeera)
├── ingest.py                  # RSS parser + Trafilatura scraper + FastEmbed hybrid indexer
├── rag.py                     # Time-aware hybrid search + recency decay + Gemini synthesis
└── requirements.txt           # Project dependencies
```

### The 4 Workspaces

1. **🌐 Intelligence Radar (`app.py`):**
   - Infinite-scroll breaking wire ticker marquee.
   - Dynamic article clustering grouped into active storylines.
   - Source distribution breakdown across global wires.
   - Latest wire dispatches stream with relative timestamp badges.

2. **🔍 Deep Explainer (`pages/1_Deep_Explainer.py`):**
   - Grounded LLM synthesis with inline citations and the consensus/conflict breakdown.
   - **Corroboration Rating Card:** Shows whether an event has high multi-wire corroboration or single-outlet status.
   - **Interactive Story Milestone Scrubber:** Slider that lets you rewind and step through the reporting sequence event-by-event.
   - Relevance match bars and raw diagnostic viewer.

3. **⚖️ Cross-Wire Analysis (`pages/2_Cross_Wire_Analysis.py`):**
   - Side-by-side comparison of any story across two different newsrooms (e.g. BBC World vs. Al Jazeera).
   - **The Omission Detector:** Identifies details and quotes that one outlet included while the other omitted.
   - Tone, vocabulary, and framing angle divergence analysis.
   - Preset buttons for quick one-click cross-outlet comparisons.

4. **🕸️ Entity Knowledge Graph (`pages/3_Entity_Graph.py`):**
   - Extracts named entities (people, organizations, locations) using spaCy NER.
   - Interactive physics-based network canvas powered by vis.js forceAtlas2.
   - Entity co-occurrence matrix and frequency distribution table.

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Initial News Ingestion
Fetches articles from configured feeds, cleans them with `trafilatura`, chunks them, and stores dense + BM25 sparse vectors into `./qdrant_db`:
```bash
python ingest.py
```

### 3. Launch the Streamlit App
```bash
streamlit run app.py
```

### 4. Provide your Free Google Gemini API Key
- Enter your key in the Streamlit sidebar (obtainable for free at [Google AI Studio](https://aistudio.google.com/)).
- Or export it as an environment variable:
  ```bash
  export GEMINI_API_KEY="your-api-key-here"
  ```

---

## 🧪 Evaluation Benchmark

Run the retrieval precision benchmark against a calibrated question set:
```bash
python eval_benchmark.py
```
This tests Top-3 and Top-5 entity recall to verify hybrid search accuracy.
