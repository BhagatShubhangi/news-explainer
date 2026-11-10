import sys
import json
from rag import NewsRAGEngine

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

engine = NewsRAGEngine()
query = "What happened in the Krakow shooting?"
results = engine.retrieve(query=query, top_k=3)

print("=" * 60)
print(f"QUERY: {query}")
print("=" * 60)
for i, r in enumerate(results, 1):
    print(f"\n[Result {i}] {r['title']}")
    print(f"Source: {r['source']} | Date: {r['published_date']}")
    print(f"URL: {r['url']}")
    print(f"Score: {r['score']:.4f} (RRF: {r['rrf_score']:.4f})")
    print(f"Excerpt: {r['text'][:200]}...")

prompt = engine.build_rag_prompt(query, results)
print("\n" + "=" * 60)
print("GENERATED PROMPT PREVIEW:")
print("=" * 60)
print(prompt[:600] + "\n...[truncated for display]...")
