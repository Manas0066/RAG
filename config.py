"""
RAG Configuration (Clean Version)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# 🔑 API Key
GEMINI_API_KEY = os.getenv("AIzaSyAsbHJzLai7xx0ey6OjcJdQqipRpsMgPx8")

# 📂 Paths
PDF_PATH = os.getenv("PDF_PATH", "data/ExplosivesRules2008.pdf")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FAISS_INDEX_DIR = os.path.join(BASE_DIR, "indices", "faiss_index")

# ⚙️ Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# 🔍 Retrieval
TOP_K = int(os.getenv("TOP_K", "3"))