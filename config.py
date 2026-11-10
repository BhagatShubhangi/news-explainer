import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
QDRANT_STORAGE_PATH = str(BASE_DIR / "qdrant_db")
FEEDS_FILE = str(BASE_DIR / "feeds.json")
SQLITE_DB_PATH = str(BASE_DIR / "articles.db")

# Qdrant Collection Settings
COLLECTION_NAME = "news_articles"
DENSE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL_NAME = "Qdrant/bm25"

# LLM Settings
# Free tier model on Google AI Studio
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

# Ingestion Settings
MAX_ARTICLES_PER_FEED = 10
CHUNK_SIZE = 500  # characters/words
CHUNK_OVERLAP = 50
SIMILARITY_DEDUP_THRESHOLD = 0.88  # Cosine similarity for deduplication
