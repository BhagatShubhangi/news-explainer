import json
import logging
import sys
import time
from typing import Dict, List

from rag import NewsRAGEngine

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 20 Evaluative Benchmark Questions covering various topics and entity queries
BENCHMARK_DATASET = [
    {
        "id": 1,
        "query": "Krakow shooting suspect condition",
        "expected_keywords": ["krakow", "shooting", "hospital", "police", "suspect"],
    },
    {
        "id": 2,
        "query": "Train crash injuries and casualties in Europe",
        "expected_keywords": ["train", "dead", "injured", "collision"],
    },
    {
        "id": 3,
        "query": "Pope Francis remarks on austerity and economic policy",
        "expected_keywords": ["pope", "austerity", "milei", "economic"],
    },
    {
        "id": 4,
        "query": "French drug gangs recruiting minors and children",
        "expected_keywords": ["french", "drug", "gang", "children", "youth"],
    },
    {
        "id": 5,
        "query": "Record global temperatures and climate forecast",
        "expected_keywords": ["hottest", "temperature", "climate", "record", "scientists"],
    },
    {
        "id": 6,
        "query": "Government electric vehicle target adjustments",
        "expected_keywords": ["ev", "electric", "target", "vehicle", "government"],
    },
    {
        "id": 7,
        "query": "Bank collapse and financial regulatory probe",
        "expected_keywords": ["bank", "collapse", "regulator", "deposit"],
    },
    {
        "id": 8,
        "query": "Nvidia CEO investigation reports",
        "expected_keywords": ["nvidia", "ceo", "investigation"],
    },
    {
        "id": 9,
        "query": "NASA recruitment for astronaut missions",
        "expected_keywords": ["nasa", "astronaut", "mission", "space"],
    },
    {
        "id": 10,
        "query": "International diplomatic talks and ceasefire status",
        "expected_keywords": ["diplomatic", "talks", "ceasefire", "peace"],
    },
]


def evaluate_retrieval(engine: NewsRAGEngine, benchmark: List[Dict]) -> Dict:
    """Evaluates Precision and Keyword Recall for Top-K retrieval."""
    results = []
    top_3_hits = 0
    top_5_hits = 0

    print("=" * 60)
    print("RUNNING RAG RETRIEVAL EVALUATION BENCHMARK")
    print("=" * 60)

    for item in benchmark:
        query = item["query"]
        expected = item["expected_keywords"]

        retrieved = engine.retrieve(query=query, top_k=5)
        if not retrieved:
            results.append({"id": item["id"], "hit_top_3": False, "hit_top_5": False, "matches": []})
            continue

        matched_articles = []
        for rank, chunk in enumerate(retrieved, 1):
            text_lower = (chunk["title"] + " " + chunk["text"]).lower()
            keyword_matches = [kw for kw in expected if kw in text_lower]
            if len(keyword_matches) >= 2:  # High confidence match
                matched_articles.append((rank, chunk["title"], keyword_matches))

        hit_3 = any(rank <= 3 for rank, _, _ in matched_articles)
        hit_5 = len(matched_articles) > 0

        if hit_3:
            top_3_hits += 1
        if hit_5:
            top_5_hits += 1

        status = "PASSED" if hit_3 else ("PARTIAL (Top 5)" if hit_5 else "FAILED")
        print(f"[{status}] Q{item['id']}: '{query}' -> Found {len(matched_articles)} matches.")
        for rank, title, kws in matched_articles[:2]:
            print(f"      Rank #{rank}: {title[:55]}... (Matched: {', '.join(kws)})")

    total = len(benchmark)
    p_at_3 = (top_3_hits / total) * 100
    p_at_5 = (top_5_hits / total) * 100

    print("=" * 60)
    print(f"BENCHMARK SUMMARY:")
    print(f"Precision @ Top-3 Recall: {p_at_3:.1f}% ({top_3_hits}/{total})")
    print(f"Precision @ Top-5 Recall: {p_at_5:.1f}% ({top_5_hits}/{total})")
    print("=" * 60)

    return {
        "total_queries": total,
        "hit_top_3": top_3_hits,
        "hit_top_5": top_5_hits,
        "precision_top_3": p_at_3,
        "precision_top_5": p_at_5,
    }


if __name__ == "__main__":
    engine = NewsRAGEngine()
    evaluate_retrieval(engine, BENCHMARK_DATASET)
