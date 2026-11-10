import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models

import config

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class NewsRAGEngine:
    def __init__(self, api_key: Optional[str] = None, client: Optional[QdrantClient] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = client or QdrantClient(path=config.QDRANT_STORAGE_PATH)
        self.dense_model = TextEmbedding(model_name=config.DENSE_MODEL_NAME)
        self.sparse_model = SparseTextEmbedding(model_name=config.SPARSE_MODEL_NAME)

    def retrieve(
        self,
        query: str,
        days_back: Optional[int] = None,
        top_k: int = 12,
        time_decay_factor: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search (Dense BGE + Sparse BM25 via RRF)
        with optional date range filtering and exponential recency decay re-ranking.
        """
        # 1. Embed query
        query_dense = list(self.dense_model.embed([query]))[0].tolist()
        query_sparse = list(self.sparse_model.embed([query]))[0]

        # 2. Date filter if requested
        query_filter = None
        if days_back is not None and days_back > 0:
            now_ts = datetime.now(timezone.utc).timestamp()
            cutoff_ts = now_ts - (days_back * 86400)
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="published_timestamp",
                        range=models.Range(gte=cutoff_ts),
                    )
                ]
            )

        # 3. Hybrid search with Reciprocal Rank Fusion
        results = self.client.query_points(
            collection_name=config.COLLECTION_NAME,
            prefetch=[
                models.Prefetch(
                    query=models.SparseVector(
                        indices=query_sparse.indices.tolist(),
                        values=query_sparse.values.tolist(),
                    ),
                    using="sparse",
                    limit=top_k * 2,
                    filter=query_filter,
                ),
                models.Prefetch(
                    query=query_dense,
                    using="dense",
                    limit=top_k * 2,
                    filter=query_filter,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=top_k * 2,
        )

        now_ts = datetime.now(timezone.utc).timestamp()
        reranked = []

        for p in results.points:
            payload = p.payload
            rrf_score = p.score or 0.0
            pub_ts = payload.get("published_timestamp", now_ts)

            # Calculate days elapsed since publication
            days_ago = max(0.0, (now_ts - pub_ts) / 86400.0)

            # Exponential time decay formula: Score * e^(-lambda * days_ago)
            decay_multiplier = math.exp(-time_decay_factor * days_ago)
            final_score = rrf_score * decay_multiplier

            reranked.append(
                {
                    "score": final_score,
                    "rrf_score": rrf_score,
                    "days_ago": round(days_ago, 1),
                    "title": payload.get("title", ""),
                    "source": payload.get("source", ""),
                    "url": payload.get("url", ""),
                    "published_date": payload.get("published_date", ""),
                    "category": payload.get("category", ""),
                    "chunk_index": payload.get("chunk_index", 0),
                    "text": payload.get("text", ""),
                }
            )

        # Sort by final time-weighted score descending
        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked[:top_k]

    def build_rag_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Formats the retrieved context and system instructions for Gemini."""
        context_blocks = []
        for i, c in enumerate(chunks, 1):
            context_blocks.append(
                f"[Source {i}] {c['title']} | Source: {c['source']} | Date: {c['published_date']}\n"
                f"URL: {c['url']}\n"
                f"Content: {c['text']}\n"
            )

        context_str = "\n".join(context_blocks)

        prompt = f"""You are "What Just Happened?", an objective, cited, investigative news explainer.
Answer the user's question accurately and strictly based on the provided news articles.

USER QUESTION:
"{query}"

RETRIEVED NEWS ARTICLES:
{context_str}

YOUR TASK:
Provide a comprehensive, objective response structured in clean Markdown with the following mandatory sections:

### 1. Executive Synopsis ("What Just Happened?")
- 2-3 clear paragraphs summarizing the event.
- Ground every factual statement with inline citations linking to the source index, e.g. [Source 1], [Source 3].

### 2. The Fog of War: Consensus vs. Disputed Claims
Use two subsections:
- **Verified / Broad Consensus:** Bullet points of facts where multiple outlets agree.
- **Unclear / Disputed / Conflicting:** Bullet points of conflicting numbers, unconfirmed claims, or differing accounts between outlets. If there are no major conflicts, note what remains unverified or developing.

### 3. Chronological Story Progression (Timeline)
Present a clean chronological timeline of how the story unfolded:
- **[Date / Time]** - **Event Headline:** Concise description of what developed. Cite the source [Source X].

### 4. Source Perspectives & Framing
Briefly highlight if different outlets emphasized distinct angles (e.g., humanitarian impact vs. market reaction vs. geopolitical stance).

CRITICAL RULES:
- If the retrieved context does not contain enough information to answer the question, clearly state what is known and what cannot be answered from the available reports.
- Do NOT hallucinate facts not present in the sources.
- Preserve proper nouns, acronyms, and direct quotations where relevant.
"""
        return prompt

    def generate_explanation(
        self,
        query: str,
        days_back: Optional[int] = None,
        top_k: int = 10,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Runs the complete RAG pipeline: retrieval -> prompting -> LLM generation."""
        key = api_key or self.api_key
        chunks = self.retrieve(query=query, days_back=days_back, top_k=top_k)

        if not chunks:
            return {
                "answer": "No relevant news articles found for this topic in the ingested feeds. Try widening the date filter or refreshing the feeds.",
                "sources": [],
                "prompt": "",
            }

        prompt = self.build_rag_prompt(query, chunks)

        if not key:
            return {
                "answer": (
                    "**Google Gemini API Key Required**\n\n"
                    "We successfully retrieved and reranked relevant news articles, but need an API key to synthesize the final explanation.\n\n"
                    "Please enter your free Google AI Studio API key in the sidebar."
                ),
                "sources": chunks,
                "prompt": prompt,
            }

        chosen_model = model_name or config.DEFAULT_GEMINI_MODEL
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=chosen_model,
                contents=prompt,
            )
            answer_text = response.text
        except Exception as e:
            logging.error(f"Gemini API generation error: {e}")
            answer_text = f"**Error generating response:** {e}"

        return {
            "answer": answer_text,
            "sources": chunks,
            "prompt": prompt,
        }
