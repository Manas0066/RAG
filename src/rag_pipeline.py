"""
Simple RAG Pipeline (Gemini + FAISS)
Clean, fast, production-style pipeline.
"""
from google import genai
import os
import sys
from typing import Optional, Dict, Any


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PDF_PATH, FAISS_INDEX_DIR
from pdf_processor import process_pdf, build_combined_documents
from semantic_chunker import semantic_chunk_documents
from vector_store import VectorStore

# ✅ Load API Key
from dotenv import load_dotenv
load_dotenv()


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


SYSTEM_PROMPT = """
You are an expert assistant.

Use the provided context to answer the question.

If the question is general (like "what is this document about"),
try to summarize the document based on the context.

If exact answer is not present, give the best possible answer based on context.

Context:
{context}
"""


class RAGPipeline:

    def __init__(self):
        self.vector_store: Optional[VectorStore] = None
        self._is_ready = False

    def ingest(self, pdf_path: str = None):
        """Process PDF and build FAISS index"""

        pdf_path = pdf_path or PDF_PATH

        print("\n[STEP 1] Parsing PDF...")
        parsed = process_pdf(pdf_path)
        combined = build_combined_documents(parsed)

        print("\n[STEP 2] Chunking...")
        chunks = semantic_chunk_documents(combined)

        print("\n[STEP 3] Creating FAISS index...")
        self.vector_store = VectorStore()
        self.vector_store.create_index(chunks)

        print("\n✓ INGESTION COMPLETE")

    def load(self):
        """Load FAISS index"""
        self.vector_store = VectorStore()
        self.vector_store.load_index()
        self._is_ready = True
        print("[Pipeline] Ready")

    def query(self, question: str) -> Dict[str, Any]:
        """Simple RAG query"""

        if not self._is_ready:
            self.load()

        # Step 1: Retrieve
        docs = self.vector_store.similarity_search(question, k=6)

        context = "\n\n---\n\n".join([d.page_content for d in docs])

        # Step 2: Prompt
        prompt = SYSTEM_PROMPT.format(context=context) + f"\n\nQuestion: {question}"

        # Step 3: Generate answer
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
        )

        answer = response.text

        # Step 4: Format output
        sources = [
            {
                "content": d.page_content[:200],
                "page": d.metadata.get("page", "N/A"),
            }
            for d in docs
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    def query_simple(self, question: str) -> str:
        return self.query(question)["answer"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest", action="store_true")
    parser.add_argument("--query", type=str)

    args = parser.parse_args()

    pipeline = RAGPipeline()

    if args.ingest:
        pipeline.ingest()

    elif args.query:
        result = pipeline.query(args.query)

        print("\nQuestion:", result["question"])
        print("\nAnswer:", result["answer"])

        print("\nSources:")
        for s in result["sources"]:
            print(f"Page {s['page']}: {s['content'][:100]}...")