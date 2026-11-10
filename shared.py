"""
Shared utilities, engine initialization, and topic clustering for the multi-page app.
All pages import from here to share a single Qdrant client and RAG engine instance.
"""

import os
import re
import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import streamlit as st
from qdrant_client import QdrantClient, models

import config
from rag import NewsRAGEngine
from ingest import NewsIngestor


@st.cache_resource
def get_rag_engine():
    """Singleton RAG engine shared across all pages."""
    return NewsRAGEngine()


def get_stats() -> int:
    """Returns total indexed chunk count."""
    rag = get_rag_engine()
    try:
        collections = [c.name for c in rag.client.get_collections().collections]
        if config.COLLECTION_NAME in collections:
            return rag.client.count(config.COLLECTION_NAME).count
    except Exception:
        pass
    return 0


@st.cache_data(ttl=120)
def get_all_articles() -> List[Dict]:
    """Retrieves all unique articles (chunk_index=0 only) from the index."""
    rag = get_rag_engine()
    try:
        all_points = []
        offset = None
        while True:
            points, next_offset = rag.client.scroll(
                collection_name=config.COLLECTION_NAME,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="chunk_index",
                            match=models.MatchValue(value=0),
                        )
                    ]
                ),
                limit=200,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            all_points.extend(points)
            if next_offset is None:
                break
            offset = next_offset

        articles = []
        seen_urls = set()
        for p in all_points:
            url = p.payload.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            articles.append(p.payload)
        return articles
    except Exception:
        return []


# Common stop words for topic extraction
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "dare",
    "it", "its", "he", "she", "they", "we", "you", "i", "my", "your",
    "his", "her", "their", "our", "this", "that", "these", "those",
    "what", "which", "who", "whom", "how", "where", "when", "why",
    "not", "no", "nor", "as", "if", "then", "than", "too", "very",
    "just", "about", "up", "out", "so", "after", "before", "between",
    "under", "over", "again", "more", "most", "some", "any", "each",
    "all", "both", "few", "other", "into", "through", "during", "while",
    "says", "said", "new", "also", "news", "amid", "set", "make", "makes",
    "get", "gets", "got", "take", "takes", "took", "many", "much",
    "one", "two", "three", "four", "five", "first", "last", "us",
    "here", "there", "now", "still", "even", "well", "back", "like",
}


def _extract_topic_words(title: str) -> List[str]:
    """Extract meaningful words from an article title."""
    title = re.sub(r"[^a-zA-Z\s'-]", "", title.lower())
    words = title.split()
    return [w for w in words if w not in _STOP_WORDS and len(w) > 2]


def cluster_articles(articles: List[Dict], max_clusters: int = 6) -> List[Dict]:
    """
    Groups articles into topic clusters using keyword overlap.
    Returns a list of cluster dicts with: topic, articles, keywords, source_set.
    """
    if not articles:
        return []

    # Extract keywords per article
    article_keywords = []
    for art in articles:
        kws = _extract_topic_words(art.get("title", ""))
        article_keywords.append(set(kws))

    # Count global keyword frequency
    global_freq = Counter()
    for kw_set in article_keywords:
        for w in kw_set:
            global_freq[w] += 1

    # Find significant keywords (appear in 2+ articles)
    sig_keywords = {w for w, c in global_freq.items() if c >= 2}

    # Build clusters: group articles by their most significant shared keyword
    clusters_map = defaultdict(list)
    assigned = set()

    # Sort significant keywords by frequency (most common first)
    sorted_keywords = sorted(sig_keywords, key=lambda w: -global_freq[w])

    for anchor_kw in sorted_keywords:
        if len(clusters_map) >= max_clusters:
            break

        cluster_articles_list = []
        for idx, (art, kw_set) in enumerate(zip(articles, article_keywords)):
            if idx in assigned:
                continue
            if anchor_kw in kw_set:
                cluster_articles_list.append(art)
                assigned.add(idx)

        if len(cluster_articles_list) >= 2:
            # Find shared keywords across cluster
            shared_kws = set.intersection(*[article_keywords[articles.index(a)] & sig_keywords for a in cluster_articles_list])
            label_words = sorted(shared_kws, key=lambda w: -global_freq[w])[:3]
            topic_label = " ".join(w.capitalize() for w in label_words) if label_words else anchor_kw.capitalize()

            sources_in_cluster = set(a.get("source", "") for a in cluster_articles_list)

            clusters_map[topic_label] = {
                "topic": topic_label,
                "articles": cluster_articles_list,
                "keywords": list(label_words),
                "sources": sources_in_cluster,
                "count": len(cluster_articles_list),
            }

    # Add remaining unassigned articles as "Other Developments"
    remaining = [articles[i] for i in range(len(articles)) if i not in assigned]
    if remaining:
        clusters_map["Other Developments"] = {
            "topic": "Other Developments",
            "articles": remaining,
            "keywords": [],
            "sources": set(a.get("source", "") for a in remaining),
            "count": len(remaining),
        }

    return list(clusters_map.values())


def get_source_counts(articles: List[Dict]) -> Dict[str, int]:
    """Returns article count per source outlet."""
    counts = Counter()
    for a in articles:
        counts[a.get("source", "Unknown")] += 1
    return dict(counts.most_common())
