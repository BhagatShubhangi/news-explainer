import hashlib
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import dateparser
import feedparser
import trafilatura
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class NewsIngestor:
    def __init__(self, client: Optional[QdrantClient] = None):
        logging.info("Initializing vector embeddings and Qdrant storage...")
        self.dense_model = TextEmbedding(model_name=config.DENSE_MODEL_NAME)
        self.sparse_model = SparseTextEmbedding(model_name=config.SPARSE_MODEL_NAME)
        self.client = client or QdrantClient(path=config.QDRANT_STORAGE_PATH)
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensures the Qdrant hybrid collection exists."""
        collections = [c.name for c in self.client.get_collections().collections]
        if config.COLLECTION_NAME not in collections:
            logging.info(f"Creating collection '{config.COLLECTION_NAME}'...")
            self.client.create_collection(
                collection_name=config.COLLECTION_NAME,
                vectors_config={
                    "dense": models.VectorParams(
                        size=384,  # BGE-small dimension
                        distance=models.Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(on_disk=False)
                    )
                },
            )
            # Create payload index on published_timestamp for fast time filtering
            self.client.create_payload_index(
                collection_name=config.COLLECTION_NAME,
                field_name="published_timestamp",
                field_schema=models.PayloadSchemaType.FLOAT,
            )
            logging.info("Collection initialized successfully.")

    def load_feeds(self) -> List[Dict]:
        """Loads configured RSS feeds from json."""
        if not os.path.exists(config.FEEDS_FILE):
            logging.warning("Feeds file not found.")
            return []
        with open(config.FEEDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_published_date(self, entry) -> (str, float):
        """Extracts standard ISO date and unix timestamp from feed entry."""
        raw_date = None
        for key in ["published", "updated", "pubDate", "created"]:
            if key in entry and entry[key]:
                raw_date = entry[key]
                break

        dt = None
        if raw_date:
            dt = dateparser.parse(raw_date)

        if not dt:
            dt = datetime.now(timezone.utc)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        iso_str = dt.isoformat()
        ts = dt.timestamp()
        return iso_str, ts

    def extract_article_content(self, url: str, fallback_summary: str) -> str:
        """Fetches full article text using trafilatura, falling back to summary."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                extracted = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False,
                )
                if extracted and len(extracted.strip()) > 150:
                    return extracted.strip()
        except Exception as e:
            logging.debug(f"Failed to scrape full text from {url}: {e}")

        # Clean fallback summary
        clean_fallback = re.sub(r"<[^>]+>", "", fallback_summary or "").strip()
        return clean_fallback

    def chunk_text(self, text: str, max_words: int = 200, overlap_words: int = 30) -> List[str]:
        """Splits article text into overlapping paragraph-friendly chunks."""
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_word_count = 0

        for p in paragraphs:
            words = p.split()
            if current_word_count + len(words) <= max_words:
                current_chunk.extend(words)
                current_word_count += len(words)
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    # Retain overlap from end of previous chunk
                    current_chunk = current_chunk[-overlap_words:] if len(current_chunk) > overlap_words else []
                    current_word_count = len(current_chunk)
                current_chunk.extend(words)
                current_word_count += len(words)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else [text]

    def is_already_ingested(self, article_url: str) -> bool:
        """Checks if URL already exists in Qdrant."""
        filter_url = models.Filter(
            must=[
                models.FieldCondition(
                    key="url",
                    match=models.MatchValue(value=article_url),
                )
            ]
        )
        points, _ = self.client.scroll(
            collection_name=config.COLLECTION_NAME,
            scroll_filter=filter_url,
            limit=1,
            with_payload=False,
        )
        return len(points) > 0

    def ingest_feed(self, feed_meta: Dict) -> int:
        """Parses a single feed and indexes new articles."""
        feed_name = feed_meta["name"]
        feed_url = feed_meta["url"]
        category = feed_meta.get("category", "General")
        logging.info(f"Fetching feed: {feed_name} ({feed_url})")

        parsed = feedparser.parse(feed_url)
        entries = parsed.entries[: config.MAX_ARTICLES_PER_FEED]
        ingested_count = 0

        for entry in entries:
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "")

            if not url or not title:
                continue

            if self.is_already_ingested(url):
                logging.debug(f"Skipping already indexed: {title[:40]}...")
                continue

            iso_date, timestamp = self.parse_published_date(entry)
            content = self.extract_article_content(url, summary)

            if len(content) < 50:
                continue

            chunks = self.chunk_text(content)
            logging.info(f"Ingesting: '{title[:50]}' ({len(chunks)} chunks) from {feed_name}")

            # Generate vectors for all chunks in batch
            dense_vecs = list(self.dense_model.embed(chunks))
            sparse_vecs = list(self.sparse_model.embed(chunks))

            points = []
            for idx, (chunk_text, d_vec, s_vec) in enumerate(zip(chunks, dense_vecs, sparse_vecs)):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}_{idx}"))
                payload = {
                    "url": url,
                    "title": title,
                    "source": feed_name,
                    "category": category,
                    "published_date": iso_date,
                    "published_timestamp": timestamp,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "text": chunk_text,
                }
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector={
                            "dense": d_vec.tolist(),
                            "sparse": models.SparseVector(
                                indices=s_vec.indices.tolist(),
                                values=s_vec.values.tolist(),
                            ),
                        },
                        payload=payload,
                    )
                )

            if points:
                self.client.upsert(
                    collection_name=config.COLLECTION_NAME,
                    points=points,
                )
                ingested_count += 1

        return ingested_count

    def run_all(self):
        """Runs ingestion across all feeds."""
        feeds = self.load_feeds()
        total_new = 0
        start_t = time.time()
        logging.info(f"Starting ingestion across {len(feeds)} feeds...")
        for feed in feeds:
            try:
                count = self.ingest_feed(feed)
                total_new += count
            except Exception as e:
                logging.error(f"Error reading feed {feed['name']}: {e}")

        duration = time.time() - start_t
        logging.info(f"Ingestion complete: {total_new} new articles indexed in {duration:.1f}s.")
        return total_new


if __name__ == "__main__":
    ingestor = NewsIngestor()
    ingestor.run_all()
