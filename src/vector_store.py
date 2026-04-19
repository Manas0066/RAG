# """
# FAISS Vector Store
# Manages FAISS index creation, loading, and similarity search.
# """

# import os
# import sys
# from typing import List, Optional
# from langchain_core.documents import Document
# from langchain_community.vectorstores import FAISS
# from langchain_ollama import OllamaEmbeddings

# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from config import OLLAMA_HOST, EMBD_MODEL, FAISS_INDEX_DIR

# os.environ["OLLAMA_HOST"] = OLLAMA_HOST


# class VectorStore:
#     """Manages FAISS vector store operations."""

#     def __init__(self, index_dir: str = None, model: str = None):
#         self.index_dir = index_dir or FAISS_INDEX_DIR
#         self.model = model or EMBD_MODEL
#         self.embeddings = OllamaEmbeddings(model=self.model)
#         self.vectorstore: Optional[FAISS] = None

#     def create_index(self, chunks: List[Document]) -> FAISS:
#         """Create FAISS index from document chunks and save to disk."""
#         print(f"[Vector Store] Creating FAISS index from {len(chunks)} chunks...")
#         self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
#         # Save to disk
#         os.makedirs(self.index_dir, exist_ok=True)
#         self.vectorstore.save_local(self.index_dir)
#         print(f"[Vector Store] ✓ Index saved to {self.index_dir}")
#         return self.vectorstore

#     def load_index(self) -> FAISS:
#         """Load existing FAISS index from disk."""
#         if not os.path.exists(self.index_dir):
#             raise FileNotFoundError(f"FAISS index not found: {self.index_dir}")
#         print(f"[Vector Store] Loading index from {self.index_dir}...")
#         self.vectorstore = FAISS.load_local(
#             self.index_dir,
#             self.embeddings,
#             allow_dangerous_deserialization=True,
#         )
#         print("[Vector Store] ✓ Index loaded")
#         return self.vectorstore

#     def index_exists(self) -> bool:
#         """Check if FAISS index exists on disk."""
#         return os.path.exists(os.path.join(self.index_dir, "index.faiss"))

#     def similarity_search(self, query: str, k: int = 10) -> List[Document]:
#         """Search for similar documents."""
#         if self.vectorstore is None:
#             self.load_index()
#         return self.vectorstore.similarity_search(query, k=k)

#     def similarity_search_with_scores(self, query: str, k: int = 10) -> List[tuple]:
#         """Search with relevance scores (lower distance = more relevant)."""
#         if self.vectorstore is None:
#             self.load_index()
#         return self.vectorstore.similarity_search_with_score(query, k=k)

#     def get_retriever(self, k: int = 10):
#         """Get a LangChain retriever interface."""
#         if self.vectorstore is None:
#             self.load_index()
#         return self.vectorstore.as_retriever(search_kwargs={"k": k})


# if __name__ == "__main__":
#     from pdf_processor import process_pdf, build_combined_documents
#     from semantic_chunker import semantic_chunk_documents

#     # Process and chunk
#     parsed = process_pdf()
#     combined = build_combined_documents(parsed)
#     chunks = semantic_chunk_documents(combined)

#     # Create vector store
#     vs = VectorStore()
#     vs.create_index(chunks)

#     # Test search
#     results = vs.similarity_search("safety distance for explosives", k=5)
#     print(f"\n--- FAISS Search: 'safety distance for explosives' ---")
#     for i, doc in enumerate(results):
#         print(f"\n  Result {i+1} (page {doc.metadata.get('page')}):")
#         print(f"  {doc.page_content[:200]}...")

"""
FAISS Vector Store
Manages FAISS index creation, loading, and similarity search.
"""

import os
import sys
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FAISS_INDEX_DIR


class VectorStore:
    """Manages FAISS vector store operations."""

    def __init__(self, index_dir: str = None):
        self.index_dir = index_dir or FAISS_INDEX_DIR

        # ✅ Replace Ollama with HuggingFace embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore: Optional[FAISS] = None

    def create_index(self, chunks: List[Document]) -> FAISS:
        """Create FAISS index from document chunks and save to disk."""
        print(f"[Vector Store] Creating FAISS index from {len(chunks)} chunks...")

        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)

        # Save to disk
        os.makedirs(self.index_dir, exist_ok=True)
        self.vectorstore.save_local(self.index_dir)

        print(f"[Vector Store] ✓ Index saved to {self.index_dir}")
        return self.vectorstore

    def load_index(self) -> FAISS:
        """Load existing FAISS index from disk."""
        if not os.path.exists(self.index_dir):
            raise FileNotFoundError(f"FAISS index not found: {self.index_dir}")

        print(f"[Vector Store] Loading index from {self.index_dir}...")

        self.vectorstore = FAISS.load_local(
            self.index_dir,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

        print("[Vector Store] ✓ Index loaded")
        return self.vectorstore

    def index_exists(self) -> bool:
        """Check if FAISS index exists on disk."""
        return os.path.exists(os.path.join(self.index_dir, "index.faiss"))

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        if self.vectorstore is None:
            self.load_index()
        return self.vectorstore.similarity_search(query, k=k)

    def similarity_search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """Search with relevance scores (lower distance = more relevant)."""
        if self.vectorstore is None:
            self.load_index()
        return self.vectorstore.similarity_search_with_score(query, k=k)

    def get_retriever(self, k: int = 5):
        """Get a LangChain retriever interface."""
        if self.vectorstore is None:
            self.load_index()
        return self.vectorstore.as_retriever(search_kwargs={"k": k})


if __name__ == "__main__":
    from pdf_processor import process_pdf, build_combined_documents
    from semantic_chunker import semantic_chunk_documents

    # Process and chunk
    parsed = process_pdf()
    combined = build_combined_documents(parsed)
    chunks = semantic_chunk_documents(combined)

    # Create vector store
    vs = VectorStore()
    vs.create_index(chunks)

    # Test search
    results = vs.similarity_search("safety distance for explosives", k=3)

    print(f"\n--- FAISS Search: 'safety distance for explosives' ---")
    for i, doc in enumerate(results):
        print(f"\n  Result {i+1} (page {doc.metadata.get('page')}):")
        print(f"  {doc.page_content[:200]}...")